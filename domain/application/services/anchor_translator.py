"""
Tradução/validação de slug de âncora semântica (RF16, UC05/A2).

O Photus B já retorna `category_code` normalizado em slug, mas o
vocabulário de âncoras conhecidas (as 10 estéticas + `tecnico`) é
definido aqui, do lado do consumidor — se o Photus B um dia
adicionar/renomear uma âncora sem o photus-uc saber, degradamos para
`GLOBAL_FALLBACK_ANCHOR` em vez de quebrar o fluxo do usuário.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

KNOWN_ANCHORS = frozenset(
    {
        "vitalidade",
        "solenidade",
        "conexao",
        "distanciamento",
        "simplicidade",
        "conflito",
        "nostalgia",
        "sublime",
        "corporativo",
        "noturno",
        "tecnico",
    }
)

GLOBAL_FALLBACK_ANCHOR = "global"


def translate_anchor(anchor_slug: str) -> str:
    normalized = (anchor_slug or "").strip().lower()
    if normalized in KNOWN_ANCHORS:
        return normalized

    logger.warning(
        "Ancora desconhecida retornada pelo Photus B: %r — usando fallback %r (RF16).",
        anchor_slug,
        GLOBAL_FALLBACK_ANCHOR,
    )
    return GLOBAL_FALLBACK_ANCHOR
