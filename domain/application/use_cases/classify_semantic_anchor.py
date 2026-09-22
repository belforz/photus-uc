"""
UC05 — Classificar Âncora Semântica (Photus B).

Ator: Sistema (acionado internamente por UC04 — relação <<include>>).
RFs relacionados: RF04, RF05, RF06, RF16, RNF01, RNF02, RNF06.

Pré-condição: EvaluationBatch já criado com input_text preenchido.
Fluxo principal:
    1. Envia o input_text para a API do Photus B.
    2. Deriva a rota de classificação a partir do resultado:
       technical=True -> tecnico; used_fallback=True -> fallback;
       caso contrário -> fast_track (RF04/RF05/RF06).
    3. Normaliza a âncora retornada contra o vocabulário conhecido
       (RF16).
    4. Persiste classified_anchor/classification_route no lote.
Fluxo alternativo A1: Photus B indisponível/timeout -> PhotusBUnavailableError
    é capturada aqui, o lote é marcado com status `erro` e o fluxo
    segue sem interromper o usuário (RNF06) — não repropaga a exceção.
Fluxo alternativo A2: âncora não reconhecida -> anchor_translator
    degrada para o fallback global sem interromper o fluxo (RF16).
"""

from __future__ import annotations

from domain.application.dtos.evaluation_batch_dto import (
    ClassifyAnchorRequest,
    ClassifyAnchorResponse,
)
from domain.application.exceptions.evaluation_batch_exceptions import (
    PhotusBUnavailableError,
)
from domain.application.interfaces.evaluation_batch_repository import (
    EvaluationBatchRepository,
)
from domain.application.interfaces.photus_b_client import PhotusBClient
from domain.application.services.anchor_translator import translate_anchor
from domain.entities.evaluation_batch import BatchStatus, ClassificationRoute


class ClassifySemanticAnchor:
    def __init__(
        self,
        batch_repository: EvaluationBatchRepository,
        photus_b_client: PhotusBClient,
    ) -> None:
        self._batch_repository = batch_repository
        self._photus_b_client = photus_b_client

    def execute(self, request: ClassifyAnchorRequest) -> ClassifyAnchorResponse:
        batch = self._batch_repository.get_by_id(request.batch_id)
        assert batch is not None, "batch deve existir — criado por UC04 antes deste include"

        try:
            result = self._photus_b_client.classify_text(request.input_text)
        except PhotusBUnavailableError:
            batch.status = BatchStatus.ERROR
            batch.classified_anchor = None
            batch.classification_route = None
            atualizado = self._batch_repository.update_classification(batch)
            return ClassifyAnchorResponse(
                batch_id=atualizado.id,
                status=atualizado.status,
                classified_anchor=atualizado.classified_anchor,
                classification_route=atualizado.classification_route,
            )

        if result.technical:
            route = ClassificationRoute.TECHNICAL
        elif result.used_fallback:
            route = ClassificationRoute.FALLBACK
        else:
            route = ClassificationRoute.FAST_TRACK

        batch.classified_anchor = translate_anchor(result.anchor)
        batch.classification_route = route
        batch.status = BatchStatus.PROCESSING
        atualizado = self._batch_repository.update_classification(batch)

        return ClassifyAnchorResponse(
            batch_id=atualizado.id,
            status=atualizado.status,
            classified_anchor=atualizado.classified_anchor,
            classification_route=atualizado.classification_route,
        )
