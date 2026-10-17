from __future__ import annotations

import pytest

from domain.application.services.phrase_number import is_singular


@pytest.mark.parametrize(
    "texto",
    [
        "A melhor foto do pôr do sol",
        "Encontre o melhor retrato vintage com iluminação natural",
        "a melhor foto das montanhas",
        "a melhor das minhas fotos",
        "Uma paisagem noturna com neblina",
        "Escolha a imagem mais nostálgica",
        "pôr do sol dourado",
        "f/1.8, ISO 200, 1/500s, 50mm, luz lateral suave.",
        "",
    ],
)
def test_frases_no_singular(texto: str) -> None:
    assert is_singular(texto) is True


@pytest.mark.parametrize(
    "texto",
    [
        "Fotos do pôr do sol",
        "fotos do ensaio",
        "As melhores fotos de casamento",
        "Retratos vintage com luz natural",
        "Mostre imagens nostálgicas",
        "Fotos com luz de fim de tarde suave, clima bucólico e nostálgico.",
        "paisagens urbanas à noite",
        "céus estrelados",
    ],
)
def test_frases_no_plural(texto: str) -> None:
    assert is_singular(texto) is False
