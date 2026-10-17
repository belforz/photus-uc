from __future__ import annotations

from datetime import UTC, datetime

from domain.application.dtos.evaluation_batch_dto import EvaluatePhotosRequest
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
A = PhotoEvaluationStatus.APPROVED
R = PhotoEvaluationStatus.REJECTED
U = PhotoEvaluationStatus.UNDEFINED


def _run(input_text: str, evaluations: list[tuple[PhotoEvaluationStatus, float]]):
    repo = FakeEvaluationBatchRepository()
    repo.create(
        EvaluationBatch(
            id="b1",
            user_id="u1",
            input_text=input_text,
            status=BatchStatus.PROCESSING,
            classified_anchor="sublime",
            classification_route=ClassificationRoute.FAST_TRACK,
            created_at=NOW,
        )
    )
    repo.add_photos(
        [
            EvaluatedPhoto(
                id=f"p{i}",
                batch_id="b1",
                file_name=f"foto_{i}.jpg",
                file_path=f"/x/foto_{i}.jpg",
                evaluation_status=PhotoEvaluationStatus.PENDING,
                created_at=NOW,
            )
            for i in range(len(evaluations))
        ]
    )
    pipeline = FakePhotoEvaluationPipeline(
        outcome=PipelineOutcome(
            results=[
                PhotoEvaluationResult(f"foto_{i}.jpg", status, score)
                for i, (status, score) in enumerate(evaluations)
            ],
            thresholds_file="sublime_thresholds.json",
            thresholds_source="specific",
        )
    )
    EvaluatePhotos(repo, pipeline).execute(EvaluatePhotosRequest("b1"))
    return {p.file_name: p.is_top3 for p in repo.list_photos("b1")}


def test_tc_s4_06_singular_marca_as_3_aprovadas_de_maior_score() -> None:
    marcadas = _run(
        "A melhor foto do pôr do sol",
        [(A, 0.70), (A, 0.95), (A, 0.80), (A, 0.60), (R, 0.99)],
    )

    assert marcadas == {
        "foto_0.jpg": True,
        "foto_1.jpg": True,
        "foto_2.jpg": True,
        "foto_3.jpg": False,
        "foto_4.jpg": False,  # reprovada nunca entra, mesmo com score alto
    }


def test_tc_s4_07_plural_nao_marca_nenhuma_foto() -> None:
    marcadas = _run("Fotos do pôr do sol", [(A, 0.9), (A, 0.8), (A, 0.7)])

    assert not any(marcadas.values())


def test_tc_s4_08_menos_de_3_aprovadas_marca_so_as_disponiveis() -> None:
    marcadas = _run("A melhor foto do pôr do sol", [(A, 0.9), (A, 0.8), (R, 0.1), (U, 0.4)])

    assert marcadas == {
        "foto_0.jpg": True,
        "foto_1.jpg": True,
        "foto_2.jpg": False,
        "foto_3.jpg": False,
    }


def test_singular_sem_nenhuma_aprovada_nao_marca_nada() -> None:
    assert not any(_run("o melhor retrato", [(R, 0.1), (U, 0.4)]).values())


def test_empate_de_score_desempata_pelo_nome_do_arquivo() -> None:
    marcadas = _run("o melhor retrato", [(A, 0.8), (A, 0.8), (A, 0.8), (A, 0.8)])

    assert [n for n, top in marcadas.items() if top] == ["foto_0.jpg", "foto_1.jpg", "foto_2.jpg"]
