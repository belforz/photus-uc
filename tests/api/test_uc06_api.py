
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.deps import get_evaluation_job, get_photo_storage, get_photus_b_client
from domain.application.exceptions.evaluation_batch_exceptions import (
    EvaluationEngineError,
    PhotusBUnavailableError,
)
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationResult,
    PipelineOutcome,
)
from domain.application.interfaces.photus_b_client import SemanticClassification
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.jobs.evaluation_job import SessionEvaluationJob
from main import app
from tests.fakes import FakePhotoEvaluationPipeline, FakePhotoStorage, FakePhotusBClient


@pytest.fixture(autouse=True)
def _fakes(client: TestClient) -> Iterator[None]:
    app.dependency_overrides[get_photo_storage] = lambda: FakePhotoStorage()
    app.dependency_overrides[get_photus_b_client] = lambda: FakePhotusBClient(
        result=SemanticClassification(
            anchor="sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    yield


def _use_pipeline(client: TestClient, pipeline: FakePhotoEvaluationPipeline) -> None:
    job = SessionEvaluationJob(client.testing_session_factory, pipeline)
    app.dependency_overrides[get_evaluation_job] = lambda: job


def _headers(client: TestClient, email: str = "leandro@teste.com") -> dict[str, str]:
    client.post(
        "/usuarios",
        json={
            "nome": "Usuario",
            "email": email,
            "senha": "SenhaForte#123",
            "tipo_usuario": "fotografo",
        },
    )
    login = client.post("/auth/login", json={"email": email, "senha": "SenhaForte#123"}).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _photos(n: int) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("photos", (f"foto_{i}.jpg", b"x", "image/jpeg")) for i in range(n)]


def _ok_outcome(n: int) -> PipelineOutcome:
    return PipelineOutcome(
        results=[
            PhotoEvaluationResult(
                file_name=f"foto_{i}.jpg",
                status=PhotoEvaluationStatus.APPROVED if i % 2 == 0 else PhotoEvaluationStatus.REJECTED,
                final_score=0.8 if i % 2 == 0 else 0.2,
                metrics={"sharpness": 100.0 + i, "edge_density": 0.3, "exposure_ratio": 0.1},
                face_metrics={"confidence": 0.0},
            )
            for i in range(n)
        ],
        thresholds_file="sublime_thresholds.json",
        thresholds_source="specific",
    )


def test_tc_s3_07_lote_de_5_fotos_persiste_5_avaliacoes_e_conclui(client: TestClient) -> None:
    pipeline = FakePhotoEvaluationPipeline(outcome=_ok_outcome(5))
    _use_pipeline(client, pipeline)
    headers = _headers(client)

    criado = client.post(
        "/batches", headers=headers, data={"input_text": "luz suave"}, files=_photos(5)
    )
    assert criado.status_code == 201
    assert criado.json()["status"] == "em_processamento"  # resposta imediata, antes do UC06

    detalhe = client.get(f"/batches/{criado.json()['id']}", headers=headers)

    assert detalhe.status_code == 200
    corpo = detalhe.json()
    assert corpo["status"] == "concluido"
    assert corpo["total_photos"] == 5
    assert corpo["evaluated_photos"] == 5
    assert corpo["thresholds_file"] == "sublime_thresholds.json"
    assert len(corpo["photos"]) == 5
    for foto in corpo["photos"]:
        assert foto["evaluation_status"] in {"aprovado", "reprovado"}
        assert foto["final_score"] is not None
        assert foto["metrics_json"]["metrics"]["sharpness"] >= 100.0
    assert pipeline.calls[0][1] == "sublime"


def test_tc_s3_09_falha_do_engine_marca_lote_erro_e_a_api_continua_de_pe(
    client: TestClient,
) -> None:
    _use_pipeline(
        client,
        FakePhotoEvaluationPipeline(error=EvaluationEngineError("exit=139")),
    )
    headers = _headers(client)

    criado = client.post(
        "/batches", headers=headers, data={"input_text": "luz suave"}, files=_photos(2)
    )
    detalhe = client.get(f"/batches/{criado.json()['id']}", headers=headers)

    assert criado.status_code == 201
    assert detalhe.json()["status"] == "erro"
    assert detalhe.json()["evaluated_photos"] == 0
    assert client.get("/health").json() == {"status": "ok"}


def test_excecao_inesperada_no_job_nao_deixa_o_lote_preso_em_processamento(
    client: TestClient,
) -> None:
    _use_pipeline(client, FakePhotoEvaluationPipeline(error=RuntimeError("bug inesperado")))
    headers = _headers(client)

    criado = client.post(
        "/batches", headers=headers, data={"input_text": "luz suave"}, files=_photos(1)
    )

    assert client.get(f"/batches/{criado.json()['id']}", headers=headers).json()["status"] == "erro"


def test_uc05_com_photus_b_fora_nao_dispara_avaliacao_tecnica(client: TestClient) -> None:
    pipeline = FakePhotoEvaluationPipeline(outcome=_ok_outcome(1))
    _use_pipeline(client, pipeline)
    app.dependency_overrides[get_photus_b_client] = lambda: FakePhotusBClient(
        error=PhotusBUnavailableError("timeout")
    )
    headers = _headers(client)

    criado = client.post(
        "/batches", headers=headers, data={"input_text": "luz suave"}, files=_photos(1)
    )

    assert criado.json()["status"] == "erro"
    assert pipeline.calls == []  # pré-condição do UC06: sem âncora, sem avaliação


def test_get_lote_de_outro_usuario_retorna_403(client: TestClient) -> None:
    _use_pipeline(client, FakePhotoEvaluationPipeline(outcome=_ok_outcome(1)))
    dono = _headers(client, "dono@teste.com")
    outro = _headers(client, "outro@teste.com")
    criado = client.post(
        "/batches", headers=dono, data={"input_text": "luz suave"}, files=_photos(1)
    )

    resposta = client.get(f"/batches/{criado.json()['id']}", headers=outro)

    # Sprint 4 / RF14: existe mas é de outro usuário => 403 (inexistente segue 404).
    assert resposta.status_code == 403


def test_get_lote_inexistente_retorna_404(client: TestClient) -> None:
    assert client.get("/batches/nao-existe", headers=_headers(client)).status_code == 404


def test_get_lote_sem_autenticacao_retorna_401(client: TestClient) -> None:
    assert client.get("/batches/qualquer").status_code == 401
