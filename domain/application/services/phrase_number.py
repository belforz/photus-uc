from __future__ import annotations

import re
import unicodedata

# UC09 / RF11 — a frase original está no singular ("a melhor foto do pôr do
# sol") ou no plural ("fotos do pôr do sol")? Só frases no singular recebem o
# recorte Top 3; no plural o front exibe a galeria completa.
#
# Heurística lexical para português, sem NLP pesado: varre os tokens em ordem e
# o PRIMEIRO que for marcador de número decide (o núcleo da frase quase sempre
# vem antes de seus complementos: "a melhor foto DAS montanhas" é singular
# embora "montanhas" seja plural). Sem marcador, olha o primeiro termo de
# conteúdo terminado em "s". Na dúvida, singular — o pior caso é destacar o
# Top 3 de uma busca no plural, e a galeria completa continua logo abaixo.

_NOUNS_SINGULAR = frozenset(
    {
        "foto", "fotografia", "imagem", "retrato", "paisagem", "clique",
        "registro", "cena", "momento", "captura", "selfie", "autorretrato",
        "panorama", "close", "enquadramento", "shot",
    }
)
_NOUNS_PLURAL = frozenset(
    {
        "fotos", "fotografias", "imagens", "retratos", "paisagens", "cliques",
        "registros", "cenas", "momentos", "capturas", "selfies",
        "autorretratos", "panoramas", "closes", "enquadramentos", "shots",
    }
)
_MARKERS_SINGULAR = frozenset(
    {
        "a", "o", "um", "uma", "melhor", "pior", "minha", "meu", "unica",
        "unico", "esta", "este", "essa", "esse", "aquela", "aquele",
    }
)
_MARKERS_PLURAL = frozenset(
    {
        "as", "os", "uns", "umas", "melhores", "piores", "minhas", "meus",
        "todas", "todos", "varias", "varios", "muitas", "muitos", "algumas",
        "alguns", "suas", "seus", "essas", "esses", "estas", "estes",
    }
)
_SINGULAR = _NOUNS_SINGULAR | _MARKERS_SINGULAR
_PLURAL = _NOUNS_PLURAL | _MARKERS_PLURAL

# Palavras terminadas em "s" que não são plural, e contrações/preposições que
# concordam com o complemento (não com o núcleo) e por isso não contam.
_NOT_PLURAL_S = frozenset(
    {
        "mais", "menos", "pais", "tres", "lapis", "onibus", "gas", "dos",
        "das", "nos", "nas", "pelos", "pelas", "com", "sem", "apos", "atras",
        "iris", "alias", "paris", "ines", "luis", "marques",
    }
)

_TOKEN = re.compile(r"[a-z]+")


def _tokens(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return _TOKEN.findall(folded)


def is_singular(text: str) -> bool:
    tokens = _tokens(text or "")
    for token in tokens:
        if token in _PLURAL:
            return False
        if token in _SINGULAR:
            return True

    for token in tokens:
        if len(token) >= 4 and token.endswith("s") and token not in _NOT_PLURAL_S:
            return False
        if len(token) >= 4:
            break
    return True
