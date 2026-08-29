"""
Testes de integração HTTP para UC01-UC03, cobrindo a matriz TC-S1-*.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _cadastrar(client: TestClient, email: str = "leandro@teste.com") -> dict:
    resposta = client.post(
        "/usuarios",
        json={
            "nome": "Leandro",
            "email": email,
            "senha": "SenhaForte#123",
            "tipo_usuario": "fotografo",
        },
    )
    assert resposta.status_code == 201
    return resposta.json()


def test_tc_s1_01_cadastro_com_sucesso(client: TestClient) -> None:
    resposta = client.post(
        "/usuarios",
        json={
            "nome": "Leandro",
            "email": "leandro@teste.com",
            "senha": "SenhaForte#123",
            "tipo_usuario": "fotografo",
        },
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Leandro"
    assert corpo["email"] == "leandro@teste.com"
    assert "id" in corpo


def test_tc_s1_03_cadastro_com_email_duplicado(client: TestClient) -> None:
    _cadastrar(client)

    resposta = client.post(
        "/usuarios",
        json={
            "nome": "Outro",
            "email": "leandro@teste.com",
            "senha": "OutraSenha#456",
            "tipo_usuario": "leigo",
        },
    )

    assert resposta.status_code == 409


def test_tc_s1_04_cadastro_com_campos_obrigatorios_vazios(client: TestClient) -> None:
    resposta = client.post(
        "/usuarios",
        json={"nome": "", "email": "nao-e-email", "senha": "123", "tipo_usuario": "leigo"},
    )

    assert resposta.status_code == 422


def test_tc_s1_05_autenticacao_com_credenciais_validas(client: TestClient) -> None:
    _cadastrar(client)

    resposta = client.post(
        "/auth/login",
        json={"email": "leandro@teste.com", "senha": "SenhaForte#123"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["access_token"]
    assert corpo["token_type"] == "bearer"


def test_tc_s1_06_autenticacao_com_senha_incorreta(client: TestClient) -> None:
    _cadastrar(client)

    resposta = client.post(
        "/auth/login",
        json={"email": "leandro@teste.com", "senha": "senha-errada"},
    )

    assert resposta.status_code == 401


def test_tc_s1_07_autenticacao_com_email_inexistente(client: TestClient) -> None:
    resposta = client.post(
        "/auth/login",
        json={"email": "ninguem@teste.com", "senha": "qualquer"},
    )

    assert resposta.status_code == 401


def test_tc_s1_08_rota_protegida_com_token_invalido(client: TestClient) -> None:
    resposta = client.patch(
        "/usuarios/me",
        json={"nome": "Novo Nome"},
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert resposta.status_code == 401


def test_tc_s1_08_rota_protegida_sem_token(client: TestClient) -> None:
    resposta = client.patch("/usuarios/me", json={"nome": "Novo Nome"})

    assert resposta.status_code == 401


def test_tc_s1_09_atualizacao_de_perfil_do_proprio_usuario(client: TestClient) -> None:
    _cadastrar(client)
    login = client.post(
        "/auth/login",
        json={"email": "leandro@teste.com", "senha": "SenhaForte#123"},
    ).json()

    resposta = client.patch(
        "/usuarios/me",
        json={"nome": "Leandro Belfor"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Leandro Belfor"


def test_tc_s1_10_atualizacao_para_email_duplicado(client: TestClient) -> None:
    _cadastrar(client, email="leandro@teste.com")
    _cadastrar(client, email="outro@teste.com")
    login = client.post(
        "/auth/login",
        json={"email": "leandro@teste.com", "senha": "SenhaForte#123"},
    ).json()

    resposta = client.patch(
        "/usuarios/me",
        json={"email": "outro@teste.com"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )

    assert resposta.status_code == 409
