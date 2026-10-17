from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.deps import get_evaluation_job, get_photo_storage, get_photus_b_client
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationResult,
    PipelineOutcome,
)
from domain.application.interfaces.photus_b_client import SemanticClassification
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.jobs.evaluation_job import SessionEvaluationJob
from infra.storage.filesystem_photo_storage import FilesystemPhotoStorage
from main import app
from tests.fakes import FakePhotoEvaluationPipeline, FakePhotusBClient

A = PhotoEvaluationStatus.APPROVED
R = PhotoEvaluationStatus.REJECTED
U = PhotoEvaluationStatus.UNDEFINED

JPEG = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


@pytest.fixture(autouse=True)
def _fakes(client: TestClient, tmp_path: Path) -> Iterator[Path]:
    uploads = tmp_path / "uploads"
    app.dependency_overrides[get_photo_storage] = lambda: FilesystemPhotoStorage(str(uploads))
    app.dependency_overrides[get_photus_b_client] = lambda: FakePhotusBClient(
        result=SemanticClassification(
            anchor="sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    yield uploads


def _use_pipeline(client: TestClient, evaluations: list[tuple[PhotoEvaluationStatus, float]]) -> None:
    outcome = PipelineOutcome(
        results=[
            PhotoEvaluationResult(
                file_name=f"foto_{i}.jpg",
                status=status,
                final_score=score,
                metrics={"sharpness": 100.0, "exposure_ratio": 0.2},
            )
            for i, (status, score) in enumerate(evaluations)
        ],
        thresholds_file="sublime_thresholds.json",
        thresholds_source="specific",
    )
    job = SessionEvaluationJob(
        client.testing_session_factory, FakePhotoEvaluationPipeline(outcome=outcome)
    )
    app.dependency_overrides[get_evaluation_job] = lambda: job


def _headers(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/usuarios",
        json={"nome": "Usuario", "email": email, "senha": "SenhaForte#123", "tipo_usuario": "leigo"},
    )
    login = client.post("/auth/login", json={"email": email, "senha": "SenhaForte#123"}).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _submit(
    client: TestClient,
    headers: dict[str, str],
    text: str = "A melhor foto do pôr do sol",
    evaluations: list[tuple[PhotoEvaluationStatus, float]] | None = None,
) -> str:
    evaluations = evaluations or [(A, 0.9), (A, 0.8), (R, 0.2)]
    _use_pipeline(client, evaluations)
    files = [("photos", (f"foto_{i}.jpg", JPEG, "image/jpeg")) for i in range(len(evaluations))]
    resposta = client.post("/batches", headers=headers, data={"input_text": text}, files=files)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


# --------------------------------------------------------------------- UC07


def test_tc_s4_01_historico_isolado_por_usuario(client: TestClient) -> None:
    a, b = _headers(client, "a@teste.com"), _headers(client, "b@teste.com")
    ids_a = {_submit(client, a) for _ in range(3)}
    ids_b = {_submit(client, b) for _ in range(2)}

    lista_a = client.get("/batches", headers=a)
    lista_b = client.get("/batches", headers=b)

    assert lista_a.status_code == 200
    assert {item["id"] for item in lista_a.json()} == ids_a
    assert {item["id"] for item in lista_b.json()} == ids_b
    assert ids_a.isdisjoint(ids_b)


def test_tc_s4_02_usuario_sem_lotes_recebe_lista_vazia(client: TestClient) -> None:
    resposta = client.get("/batches", headers=_headers(client, "novo@teste.com"))

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_historico_traz_ancora_status_qtd_de_fotos_e_vem_do_mais_recente(
    client: TestClient,
) -> None:
    h = _headers(client, "a@teste.com")
    primeiro = _submit(client, h, evaluations=[(A, 0.9)])
    segundo = _submit(client, h, text="Fotos do ensaio", evaluations=[(A, 0.9), (R, 0.1)])

    itens = client.get("/batches", headers=h).json()

    assert [i["id"] for i in itens] == [segundo, primeiro]
    assert itens[0]["total_photos"] == 2
    assert itens[0]["classified_anchor"] == "sublime"
    assert itens[0]["status"] == "concluido"
    assert itens[0]["is_singular"] is False
    assert itens[1]["is_singular"] is True


def test_historico_sem_autenticacao_retorna_401(client: TestClient) -> None:
    assert client.get("/batches").status_code == 401


# --------------------------------------------------------------------- UC08


def test_tc_s4_03_detalhe_de_lote_concluido_traz_fotos_scores_e_metricas(
    client: TestClient,
) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(client, h)

    detalhe = client.get(f"/batches/{batch_id}", headers=h).json()

    assert detalhe["status"] == "concluido"
    assert len(detalhe["photos"]) == 3
    for foto in detalhe["photos"]:
        assert foto["final_score"] is not None
        assert foto["metrics_json"]["metrics"]["sharpness"] == 100.0


def test_tc_s4_04_acesso_a_lote_de_terceiro_e_negado_com_403(client: TestClient) -> None:
    dono, outro = _headers(client, "dono@teste.com"), _headers(client, "outro@teste.com")
    batch_id = _submit(client, dono)

    assert client.get(f"/batches/{batch_id}", headers=outro).status_code == 403
    foto_id = client.get(f"/batches/{batch_id}", headers=dono).json()["photos"][0]["id"]
    assert (
        client.get(f"/batches/{batch_id}/photos/{foto_id}/image", headers=outro).status_code == 403
    )


def test_tc_s4_05_lote_em_processamento_responde_status_parcial(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")
    # job padrão do conftest é um no-op: o lote fica em_processamento
    app.dependency_overrides[get_evaluation_job] = lambda: (lambda batch_id: None)
    files = [("photos", (f"foto_{i}.jpg", JPEG, "image/jpeg")) for i in range(2)]
    batch_id = client.post("/batches", headers=h, data={"input_text": "luz"}, files=files).json()[
        "id"
    ]

    detalhe = client.get(f"/batches/{batch_id}", headers=h)

    assert detalhe.status_code == 200
    corpo = detalhe.json()
    assert corpo["status"] == "em_processamento"
    assert corpo["total_photos"] == 2
    assert corpo["evaluated_photos"] == 0
    assert all(f["evaluation_status"] == "pendente" for f in corpo["photos"])


def test_foto_do_lote_e_servida_ao_proprietario(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(client, h)
    foto_id = client.get(f"/batches/{batch_id}", headers=h).json()["photos"][0]["id"]

    imagem = client.get(f"/batches/{batch_id}/photos/{foto_id}/image", headers=h)

    assert imagem.status_code == 200
    assert imagem.content == JPEG
    assert client.get(f"/batches/{batch_id}/photos/nao-existe/image", headers=h).status_code == 404


# --------------------------------------------------------------------- UC09


def test_tc_s4_06_singular_expoe_is_singular_e_marca_top3(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(
        client, h, "A melhor foto do pôr do sol", [(A, 0.7), (A, 0.95), (A, 0.8), (A, 0.6)]
    )

    detalhe = client.get(f"/batches/{batch_id}", headers=h).json()

    assert detalhe["is_singular"] is True
    top3 = {f["file_name"] for f in detalhe["photos"] if f["is_top3"]}
    assert top3 == {"foto_0.jpg", "foto_1.jpg", "foto_2.jpg"}


def test_tc_s4_07_plural_nao_marca_top3(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(client, h, "Fotos do pôr do sol", [(A, 0.9), (A, 0.8), (A, 0.7)])

    detalhe = client.get(f"/batches/{batch_id}", headers=h).json()

    assert detalhe["is_singular"] is False
    assert not any(f["is_top3"] for f in detalhe["photos"])


def test_tc_s4_08_menos_de_3_aprovadas_destaca_so_as_disponiveis(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(client, h, "A melhor foto do pôr do sol", [(A, 0.9), (A, 0.8), (R, 0.1)])

    resposta = client.get(f"/batches/{batch_id}", headers=h)
    assert resposta.status_code == 200, resposta.text
    detalhe = resposta.json()

    assert sum(f["is_top3"] for f in detalhe["photos"]) == 2


# --------------------------------------------------------------------- UC10


def test_tc_s4_09_exclusao_remove_lote_fotos_e_arquivos(
    client: TestClient, _fakes: Path
) -> None:
    h = _headers(client, "a@teste.com")
    batch_id = _submit(client, h)
    manter = _submit(client, h)
    assert (_fakes / batch_id / "foto_0.jpg").is_file()

    resposta = client.delete(f"/batches/{batch_id}", headers=h)

    assert resposta.status_code == 204
    assert client.get(f"/batches/{batch_id}", headers=h).status_code == 404
    assert [i["id"] for i in client.get("/batches", headers=h).json()] == [manter]
    assert not (_fakes / batch_id).exists()
    assert (_fakes / manter / "foto_0.jpg").is_file()  # outros lotes intactos
    # as fotos avaliadas sumiram do banco (cascata)
    from infra.db.models import EvaluatedPhotoModel

    with client.testing_session_factory() as session:
        restantes = session.query(EvaluatedPhotoModel).filter_by(batch_id=batch_id).count()
    assert restantes == 0


def test_tc_s4_10_exclusao_de_lote_de_terceiro_retorna_403_e_preserva_dados(
    client: TestClient, _fakes: Path
) -> None:
    dono, outro = _headers(client, "dono@teste.com"), _headers(client, "outro@teste.com")
    batch_id = _submit(client, dono)

    resposta = client.delete(f"/batches/{batch_id}", headers=outro)

    assert resposta.status_code == 403
    assert client.get(f"/batches/{batch_id}", headers=dono).json()["total_photos"] == 3
    assert (_fakes / batch_id / "foto_0.jpg").is_file()


def test_excluir_lote_inexistente_retorna_404(client: TestClient) -> None:
    h = _headers(client, "a@teste.com")

    assert client.delete("/batches/nao-existe", headers=h).status_code == 404


def test_excluir_sem_autenticacao_retorna_401(client: TestClient) -> None:
    assert client.delete("/batches/qualquer").status_code == 401
