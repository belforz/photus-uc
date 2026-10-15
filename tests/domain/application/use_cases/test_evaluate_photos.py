
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from domain.application.dtos.evaluation_batch_dto import EvaluatePhotosRequest
from domain.application.exceptions.evaluation_batch_exceptions import (
    AnchorNotClassifiedError,
    BatchNotFoundError,
    EvaluationEngineError,
)
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationResult,
    PipelineOutcome,
)
from domain.application.use_cases.evaluate_photos import EvaluatePhotos
from domain.entities.evaluated_photo import EvaluatedPhoto, PhotoEvaluationStatus
from domain.entities.evaluation_batch import (
    BatchStatus,
    ClassificationRoute,
    EvaluationBatch,
)
from tests.fakes import FakeEvaluationBatchRepository, FakePhotoEvaluationPipeline

NOW = datetime.now(UTC)


def _repo(
    n_photos: int = 5, anchor: str | None = "vintage"
) -> FakeEvaluationBatchRepository:
    repo = FakeEvaluationBatchRepository()
    repo.create(
        EvaluationBatch(
            id="batch-1",
            user_id="user-1",
            input_text="fotos antigas, tom quente",
            status=BatchStatus.PROCESSING,
            classified_anchor=anchor,
            classification_route=ClassificationRoute.FAST_TRACK if anchor else None,
            created_at=NOW,
        )
    )
    repo.add_photos(
        [
            EvaluatedPhoto(
                id=f"photo-{i}",
                batch_id="batch-1",
                file_name=f"foto_{i}.jpg",
                file_path=f"/fake/batch-1/foto_{i}.jpg",
                evaluation_status=PhotoEvaluationStatus.PENDING,
                created_at=NOW,
            )
            for i in range(n_photos)
        ]
    )
    return repo


def _result(i: int, status: PhotoEvaluationStatus, score: float | None, **kw) -> PhotoEvaluationResult:
    return PhotoEvaluationResult(
        file_name=f"foto_{i}.jpg",
        status=status,
        final_score=score,
        metrics={"sharpness": 142.5, "edge_density": 0.28, "exposure_ratio": 0.85},
        face_metrics={"confidence": 0.94},
        **kw,
    )


def _outcome(results, file="vintage_thresholds.json", source="specific") -> PipelineOutcome:
    return PipelineOutcome(results=results, thresholds_file=file, thresholds_source=source)


def test_tc_s3_07_persiste_um_registro_por_foto_e_conclui_o_lote() -> None:
    repo = _repo(n_photos=5)
    statuses = [
        PhotoEvaluationStatus.APPROVED,
        PhotoEvaluationStatus.APPROVED,
        PhotoEvaluationStatus.UNDEFINED,
        PhotoEvaluationStatus.REJECTED,
        PhotoEvaluationStatus.HUMAN_REVIEW,
    ]
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome([_result(i, s, 0.2 * i + 0.1) for i, s in enumerate(statuses)])
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.status == BatchStatus.COMPLETED
    assert resposta.evaluated_photos == 5
    assert repo.get_by_id("batch-1").status == BatchStatus.COMPLETED
    fotos = repo.list_photos("batch-1")
    assert len(fotos) == 5
    assert [f.evaluation_status for f in fotos] == statuses
    for i, foto in enumerate(fotos):
        assert foto.final_score == pytest.approx(0.2 * i + 0.1)
        payload = json.loads(foto.metrics_json)
        assert payload["metrics"]["sharpness"] == 142.5
        assert payload["face_metrics"] == {"confidence": 0.94}


def test_envia_ao_engine_a_ancora_do_lote_e_todas_as_fotos() -> None:
    repo = _repo(n_photos=3, anchor="sublime")
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome(
            [_result(i, PhotoEvaluationStatus.APPROVED, 0.8) for i in range(3)],
            file="sublime_thresholds.json",
        )
    )

    EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    (batch_id, anchor, photos), = pipeline.calls
    assert (batch_id, anchor) == ("batch-1", "sublime")
    assert [p.file_name for p in photos] == ["foto_0.jpg", "foto_1.jpg", "foto_2.jpg"]


def test_tc_s3_03_registra_o_arquivo_de_threshold_especifico_usado() -> None:
    repo = _repo(n_photos=1)
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome([_result(0, PhotoEvaluationStatus.APPROVED, 0.9)])
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.thresholds_file == "vintage_thresholds.json"
    payload = json.loads(repo.list_photos("batch-1")[0].metrics_json)
    assert payload["thresholds_file"] == "vintage_thresholds.json"
    assert payload["thresholds_source"] == "specific"


def test_tc_s3_04_ancora_sem_threshold_especifico_usa_global_sem_interromper() -> None:
    repo = _repo(n_photos=2, anchor="global")
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome(
            [_result(i, PhotoEvaluationStatus.APPROVED, 0.7) for i in range(2)],
            file="thresholds_global.json",
            source="global",
        )
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.status == BatchStatus.COMPLETED
    assert resposta.thresholds_file == "thresholds_global.json"
    payload = json.loads(repo.list_photos("batch-1")[0].metrics_json)
    assert payload["thresholds_source"] == "global"


def test_tc_s3_05_reprovacao_por_hard_rule_e_persistida_com_o_motivo() -> None:
    repo = _repo(n_photos=1)
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome(
            [
                _result(
                    0,
                    PhotoEvaluationStatus.REJECTED,
                    0.1,
                    details="Exposição muito alta: 0.985641",
                )
            ]
        )
    )

    EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    foto = repo.list_photos("batch-1")[0]
    assert foto.evaluation_status == PhotoEvaluationStatus.REJECTED
    assert "Exposição muito alta" in json.loads(foto.metrics_json)["details"]


def test_tc_s3_09_falha_do_binario_marca_lote_erro_sem_propagar_excecao() -> None:
    repo = _repo(n_photos=3)
    pipeline = FakePhotoEvaluationPipeline(
        error=EvaluationEngineError("Photus A terminou com exit=139: segfault")
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.status == BatchStatus.ERROR
    assert repo.get_by_id("batch-1").status == BatchStatus.ERROR
    assert resposta.evaluated_photos == 0
    assert all(
        f.evaluation_status == PhotoEvaluationStatus.PENDING for f in repo.list_photos("batch-1")
    )


def test_tc_s3_09_falha_preserva_fotos_ja_avaliadas() -> None:
    repo = _repo(n_photos=3)
    pipeline = FakePhotoEvaluationPipeline(
        error=EvaluationEngineError(
            "Photus A terminou com exit=1",
            partial_results=[_result(0, PhotoEvaluationStatus.APPROVED, 0.8)],
        )
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.status == BatchStatus.ERROR
    assert resposta.evaluated_photos == 1
    fotos = repo.list_photos("batch-1")
    assert fotos[0].evaluation_status == PhotoEvaluationStatus.APPROVED
    assert fotos[0].final_score == pytest.approx(0.8)
    assert fotos[1].evaluation_status == PhotoEvaluationStatus.PENDING


def test_foto_sem_resultado_do_engine_vira_erro_e_o_lote_conclui() -> None:
    repo = _repo(n_photos=2)
    pipeline = FakePhotoEvaluationPipeline(
        outcome=_outcome([_result(0, PhotoEvaluationStatus.APPROVED, 0.8)])
    )

    resposta = EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert resposta.status == BatchStatus.COMPLETED
    fotos = repo.list_photos("batch-1")
    assert fotos[1].evaluation_status == PhotoEvaluationStatus.ERROR
    assert "não retornou resultado" in json.loads(fotos[1].metrics_json)["details"]


def test_precondicao_lote_sem_ancora_classificada_e_rejeitado() -> None:
    repo = _repo(anchor=None)
    pipeline = FakePhotoEvaluationPipeline(outcome=_outcome([]))

    with pytest.raises(AnchorNotClassifiedError):
        EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("batch-1"))

    assert pipeline.calls == []


def test_lote_inexistente_levanta_batch_not_found() -> None:
    with pytest.raises(BatchNotFoundError):
        EvaluatePhotos(FakeEvaluationBatchRepository(), FakePhotoEvaluationPipeline()).execute(
            EvaluatePhotosRequest("nao-existe")
        )
