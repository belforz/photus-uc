"""
Testes de UC05 — Classificar Âncora Semântica (Photus B).

Cobre a matriz TC-S2-04 a TC-S2-09 (parte de roteamento).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domain.application.dtos.evaluation_batch_dto import ClassifyAnchorRequest
from domain.application.exceptions.evaluation_batch_exceptions import PhotusBUnavailableError
from domain.application.interfaces.photus_b_client import SemanticClassification
from domain.application.use_cases.classify_semantic_anchor import ClassifySemanticAnchor
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute, EvaluationBatch
from tests.fakes import FakeEvaluationBatchRepository, FakePhotusBClient


def _repo_with_batch(batch_id: str = "batch-1") -> FakeEvaluationBatchRepository:
    repo = FakeEvaluationBatchRepository()
    repo.create(
        EvaluationBatch(
            id=batch_id,
            user_id="user-1",
            input_text="qualquer texto",
            status=BatchStatus.PROCESSING,
            classified_anchor=None,
            classification_route=None,
            created_at=datetime.now(UTC),
        )
    )
    return repo


def test_tc_s2_04_jargao_tecnico_classifica_rota_tecnico() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(
        result=SemanticClassification(
            anchor="tecnico", technical=True, used_fallback=False, confidence=0.47
        )
    )
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(batch_id="batch-1", input_text="f/1.8, ISO 100, 1/250s, 50mm")
    )

    assert resposta.classification_route == ClassificationRoute.TECHNICAL
    assert resposta.classified_anchor == "tecnico"
    assert resposta.status == BatchStatus.PROCESSING


def test_tc_s2_05_fast_track_sem_fallback() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(
        result=SemanticClassification(
            anchor="sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(
            batch_id="batch-1", input_text="Fotos alegres e ensolaradas na praia"
        )
    )

    assert resposta.classification_route == ClassificationRoute.FAST_TRACK
    assert resposta.classified_anchor == "sublime"


def test_tc_s2_06_fallback_via_llm_em_ambiguidade() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(
        result=SemanticClassification(
            anchor="corporativo", technical=False, used_fallback=True, confidence=0.41
        )
    )
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(
            batch_id="batch-1", input_text="queria algo diferente, meio sei lá"
        )
    )

    assert resposta.classification_route == ClassificationRoute.FALLBACK
    assert resposta.classified_anchor == "corporativo"


def test_tc_s2_07_normalizacao_de_slug_de_ancora() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(
        result=SemanticClassification(
            anchor="Sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(batch_id="batch-1", input_text="qualquer texto")
    )

    assert resposta.classified_anchor == "sublime"


def test_tc_s2_08_falha_de_mapeamento_recai_sobre_global() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(
        result=SemanticClassification(
            anchor="ancora-desconhecida", technical=False, used_fallback=False, confidence=0.7
        )
    )
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(batch_id="batch-1", input_text="qualquer texto")
    )

    assert resposta.classified_anchor == "global"
    assert resposta.status == BatchStatus.PROCESSING


def test_tc_s2_09_indisponibilidade_do_photus_b_marca_erro_sem_crash() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(error=PhotusBUnavailableError("timeout"))
    use_case = ClassifySemanticAnchor(repo, client)

    resposta = use_case.execute(
        ClassifyAnchorRequest(batch_id="batch-1", input_text="qualquer texto")
    )

    assert resposta.status == BatchStatus.ERROR
    assert resposta.classified_anchor is None
    assert resposta.classification_route is None


def test_photus_b_indisponivel_nao_propaga_excecao() -> None:
    repo = _repo_with_batch()
    client = FakePhotusBClient(error=PhotusBUnavailableError("timeout"))
    use_case = ClassifySemanticAnchor(repo, client)

    try:
        use_case.execute(ClassifyAnchorRequest(batch_id="batch-1", input_text="x"))
    except PhotusBUnavailableError:
        pytest.fail("PhotusBUnavailableError não deveria escapar do use case (RNF06)")
