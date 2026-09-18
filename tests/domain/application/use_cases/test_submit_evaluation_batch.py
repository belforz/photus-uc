"""
Testes de UC04 — Enviar Descrição + Fotografias.

Cobre a matriz TC-S2-01 a TC-S2-03.
"""

from __future__ import annotations

import pytest

from domain.application.dtos.evaluation_batch_dto import PhotoUploadRequest, SubmitBatchRequest
from domain.application.exceptions.evaluation_batch_exceptions import (
    NoPhotosAttachedError,
    PhotoLimitExceededError,
)
from domain.application.interfaces.photus_b_client import SemanticClassification
from domain.application.use_cases.classify_semantic_anchor import ClassifySemanticAnchor
from domain.application.use_cases.submit_evaluation_batch import SubmitEvaluationBatch
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute
from tests.fakes import (
    FakeEvaluationBatchRepository,
    FakePhotoStorage,
    FakePhotusBClient,
)


def _use_case(
    client: FakePhotusBClient | None = None,
) -> tuple[SubmitEvaluationBatch, FakeEvaluationBatchRepository, FakePhotoStorage]:
    repo = FakeEvaluationBatchRepository()
    storage = FakePhotoStorage()
    photus_b_client = client or FakePhotusBClient(
        result=SemanticClassification(
            anchor="sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    classify = ClassifySemanticAnchor(repo, photus_b_client)
    return SubmitEvaluationBatch(repo, storage, classify), repo, storage


def _photos(quantity: int) -> list[PhotoUploadRequest]:
    return [
        PhotoUploadRequest(file_name=f"foto_{i}.jpg", content=b"conteudo")
        for i in range(quantity)
    ]


def test_tc_s2_01_criacao_valida_de_lote() -> None:
    use_case, repo, storage = _use_case()

    resposta = use_case.execute(
        SubmitBatchRequest(
            user_id="user-1",
            input_text="Quero fotos com luz suave e dramática",
            photos=_photos(10),
        )
    )

    assert resposta.user_id == "user-1"
    assert resposta.status == BatchStatus.PROCESSING
    assert resposta.classification_route == ClassificationRoute.FAST_TRACK
    assert repo.get_by_id(resposta.id) is not None
    assert len(storage.saved) == 10


def test_tc_s2_02_limite_de_upload_excedido() -> None:
    use_case, _, _ = _use_case()

    with pytest.raises(PhotoLimitExceededError):
        use_case.execute(
            SubmitBatchRequest(
                user_id="user-1", input_text="texto qualquer", photos=_photos(21)
            )
        )


def test_tc_s2_03_submissao_sem_fotos() -> None:
    use_case, _, _ = _use_case()

    with pytest.raises(NoPhotosAttachedError):
        use_case.execute(
            SubmitBatchRequest(user_id="user-1", input_text="texto qualquer", photos=[])
        )


def test_limite_de_20_fotos_e_aceito() -> None:
    use_case, _, _ = _use_case()

    resposta = use_case.execute(
        SubmitBatchRequest(user_id="user-1", input_text="texto qualquer", photos=_photos(20))
    )

    assert resposta.id
