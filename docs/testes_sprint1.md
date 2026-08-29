# Testes — Sprint 1 (Gestão de Conta e Acesso)

Cobre UC01 (Cadastrar-se), UC02 (Autenticar-se) e UC03 (Atualizar Perfil).
22 testes automatizados, divididos em dois níveis:

- **Unitários** (`tests/domain/application/use_cases/`) — exercitam os use
  cases isolados, com repositório/hasher/token service fake (in-memory),
  sem HTTP nem banco real.
- **Integração HTTP** (`tests/api/`) — sobem a app FastAPI com
  `TestClient` contra um SQLite em memória, cobrindo a matriz TC-S1
  ponta a ponta (request → status code → payload).

Rodar tudo: `uv run pytest -q`. Rodar só um nível: `uv run pytest tests/api`
ou `uv run pytest tests/domain`.

## Matriz de rastreabilidade (TC-S1-01 a TC-S1-10)

| ID | Caso de Uso / Req | Cenário | Resultado esperado | Teste(s) |
| :--- | :--- | :--- | :--- | :--- |
| TC-S1-01 | UC01 / RF01 | Cadastro com sucesso de novo usuário | HTTP 201; registro criado | [`test_tc_s1_01_cadastro_com_sucesso`](../tests/api/test_usuario_api.py#L24) |
| TC-S1-02 | UC01 / RNF08 | Hash seguro na persistência (nunca texto plano) | `senha_hash` ≠ senha original | [`test_nunca_persiste_senha_em_texto_plano`](../tests/domain/application/use_cases/test_cadastrar_usuario.py#L50) |
| TC-S1-03 | UC01 / RF01 | Cadastro com e-mail duplicado (A1) | HTTP 409; sem duplicata | [`test_tc_s1_03_cadastro_com_email_duplicado`](../tests/api/test_usuario_api.py#L42), [`test_rejeita_email_ja_cadastrado`](../tests/domain/application/use_cases/test_cadastrar_usuario.py#L37) |
| TC-S1-04 | UC01 / RF01 | Campos obrigatórios vazios/inválidos (A2) | HTTP 422 | [`test_tc_s1_04_cadastro_com_campos_obrigatorios_vazios`](../tests/api/test_usuario_api.py#L58) |
| TC-S1-05 | UC02 / RF01, RNF09 | Autenticação com credenciais válidas | HTTP 200; JWT retornado | [`test_tc_s1_05_autenticacao_com_credenciais_validas`](../tests/api/test_usuario_api.py#L67), [`test_autentica_com_credenciais_validas`](../tests/domain/application/use_cases/test_autenticar_usuario.py#L41) |
| TC-S1-06 | UC02 / RF01 | Senha incorreta (A1) | HTTP 401; mensagem genérica | [`test_tc_s1_06_autenticacao_com_senha_incorreta`](../tests/api/test_usuario_api.py#L81), [`test_rejeita_senha_incorreta`](../tests/domain/application/use_cases/test_autenticar_usuario.py#L61) |
| TC-S1-07 | UC02 / RF01 | E-mail inexistente (A2) — evita enumeração de contas | HTTP 401; mesma mensagem genérica de TC-S1-06 | [`test_tc_s1_07_autenticacao_com_email_inexistente`](../tests/api/test_usuario_api.py#L92), [`test_rejeita_email_inexistente`](../tests/domain/application/use_cases/test_autenticar_usuario.py#L54), [`test_mensagem_de_erro_nao_distingue_email_de_senha`](../tests/domain/application/use_cases/test_autenticar_usuario.py#L72) |
| TC-S1-08 | UC02 / RNF09 | Token ausente ou inválido em rota protegida | HTTP 401 | [`test_tc_s1_08_rota_protegida_com_token_invalido`](../tests/api/test_usuario_api.py#L101), [`test_tc_s1_08_rota_protegida_sem_token`](../tests/api/test_usuario_api.py#L111) |
| TC-S1-09 | UC03 / RF02 | Atualização de perfil do próprio usuário | HTTP 200; dados atualizados | [`test_tc_s1_09_atualizacao_de_perfil_do_proprio_usuario`](../tests/api/test_usuario_api.py#L117), [`test_atualiza_nome`](../tests/domain/application/use_cases/test_atualizar_perfil.py#L45) |
| TC-S1-10 | UC03 / RF02 | Atualização para e-mail já usado por terceiro (A1) | HTTP 409; dados originais mantidos | [`test_tc_s1_10_atualizacao_para_email_duplicado`](../tests/api/test_usuario_api.py#L134), [`test_rejeita_troca_para_email_ja_usado_por_outro_usuario`](../tests/domain/application/use_cases/test_atualizar_perfil.py#L73) |

## Testes complementares (sem TC-S1 correspondente na spec original)

| Teste | O que cobre |
| :--- | :--- |
| [`test_atualiza_senha_com_rehash`](../tests/domain/application/use_cases/test_atualizar_perfil.py#L56) | Troca de senha no `AtualizarPerfil` gera novo hash |
| [`test_rejeita_usuario_inexistente`](../tests/domain/application/use_cases/test_atualizar_perfil.py#L68) | `usuario_id` inexistente → `UsuarioNaoEncontradoError` (HTTP 404) |
| [`test_atualizacao_parcial_nao_apaga_campos_nao_informados`](../tests/domain/application/use_cases/test_atualizar_perfil.py#L85) | PATCH parcial não zera campos omitidos |
| [`test_cadastra_usuario_com_dados_validos`](../tests/domain/application/use_cases/test_cadastrar_usuario.py#L21) | Caso feliz do `CadastrarUsuario` no nível de use case |

## Infraestrutura de teste

- `tests/fakes.py` — `FakeUsuarioRepository`, `FakePasswordHasher`,
  `FakeTokenService`: implementações in-memory dos ports
  (`domain/application/interfaces/`), usadas nos testes unitários.
- `tests/api/conftest.py` — fixture `client`: cria um SQLAlchemy engine
  SQLite `:memory:` (com `StaticPool`, para manter a mesma conexão viva
  entre `create_all` e as queries) e sobrescreve a dependência
  `get_session` da app real via `app.dependency_overrides`. O lifespan da
  app não é disparado nesse fixture (tabelas já vêm do schema de teste),
  evitando que o engine "de produção" (`sqlite:///./photus.db`) seja
  tocado durante os testes.

## Não coberto nesta sprint

- Rate limiting de tentativas de login.
- Refresh token / revogação de token.
- Testes de carga/performance (RNF fora do escopo funcional da Sprint 1).
