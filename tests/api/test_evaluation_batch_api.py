"""
Testes de integração HTTP para UC04-UC05, cobrindo a matriz TC-S2-*.

O Photus B é substituído por um fake via dependency override — estes
testes não fazem chamadas de rede reais.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.deps import get_photo_storage, get_photus_b_client
from domain.application.exceptions.evaluation_batch_exceptions import PhotusBUnavailableError
from domain.application.interfaces.photus_b_client import SemanticClassification
from main import app
from tests.fakes import FakePhotoStorage, FakePhotusBClient


@pytest.fixture(autouse=True)
def _fake_photo_storage(client: TestClient) -> Iterator[None]:
    app.dependency_overrides[get_photo_storage] = lambda: FakePhotoStorage()
    yield
    del app.dependency_overrides[get_photo_storage]


@pytest.fixture
def photus_b(client: TestClient) -> Iterator[FakePhotusBClient]:
    fake = FakePhotusBClient(
        result=SemanticClassification(
            anchor="sublime", technical=False, used_fallback=False, confidence=0.7
        )
    )
    app.dependency_overrides[get_photus_b_client] = lambda: fake
    yield fake
    del app.dependency_overrides[get_photus_b_client]


def _authenticated_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/usuarios",
        json={
            "nome": "Leandro",
            "email": "leandro@teste.com",
            "senha": "SenhaForte#123",
            "tipo_usuario": "fotografo",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "leandro@teste.com", "senha": "SenhaForte#123"},
    ).json()
    return {"Authorization": f"Bearer {login['access_token']}"}


def _photo_files(quantity: int) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("photos", (f"foto_{i}.jpg", b"conteudo-fake", "image/jpeg")) for i in range(quantity)
    ]


def test_tc_s2_01_criacao_valida_de_lote_via_api(
    client: TestClient, photus_b: FakePhotusBClient
) -> None:
    headers = _authenticated_headers(client)

    resposta = client.post(
        "/batches",
        headers=headers,
        data={"input_text": "Quero fotos com luz suave e dramática"},
        files=_photo_files(10),
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "em_processamento"
    assert corpo["classification_route"] == "fast_track"
    assert corpo["classified_anchor"] == "sublime"


def test_tc_s2_02_limite_de_upload_excedido_via_api(
    client: TestClient, photus_b: FakePhotusBClient
) -> None:
    headers = _authenticated_headers(client)

    resposta = client.post(
        "/batches",
        headers=headers,
        data={"input_text": "texto qualquer"},
        files=_photo_files(21),
    )

    assert resposta.status_code == 400


def test_tc_s2_03_submissao_sem_fotos_via_api(
    client: TestClient, photus_b: FakePhotusBClient
) -> None:
    headers = _authenticated_headers(client)

    resposta = client.post(
        "/batches",
        headers=headers,
        data={"input_text": "texto qualquer"},
    )

    assert resposta.status_code == 400


def test_submissao_sem_autenticacao_e_rejeitada(client: TestClient) -> None:
    resposta = client.post(
        "/batches",
        data={"input_text": "texto qualquer"},
        files=_photo_files(1),
    )

    assert resposta.status_code == 401


def test_tc_s2_09_indisponibilidade_do_photus_b_nao_derruba_a_api(
    client: TestClient,
) -> None:
    app.dependency_overrides[get_photus_b_client] = lambda: FakePhotusBClient(
        error=PhotusBUnavailableError("timeout")
    )
    try:
        headers = _authenticated_headers(client)
        resposta = client.post(
            "/batches",
            headers=headers,
            data={"input_text": "texto qualquer"},
            files=_photo_files(1),
        )
    finally:
        del app.dependency_overrides[get_photus_b_client]

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "erro"
