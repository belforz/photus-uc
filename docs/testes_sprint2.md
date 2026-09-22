# Testes — Sprint 2 (Submissão de Lote e Roteamento Semântico)

Cobre UC04 (Enviar Descrição + Fotografias) e UC05 (Classificar Âncora
Semântica via Photus B). 16 testes automatizados, divididos em dois níveis:

- **Unitários** (`tests/domain/application/use_cases/`) — exercitam os use
  cases isolados, com repositório/storage/`PhotusBClient` fake (in-memory),
  sem HTTP, banco ou rede reais.
- **Integração HTTP** (`tests/api/`) — sobem a app FastAPI com `TestClient`
  contra um SQLite em memória e um `PhotusBClient` fake via
  `app.dependency_overrides`, cobrindo a matriz TC-S2 ponta a ponta
  (multipart request → status code → payload), sem chamada de rede ao
  Photus B real.

Rodar tudo: `uv run pytest -q`. Rodar só um nível: `uv run pytest tests/api`
ou `uv run pytest tests/domain`.

## Matriz de rastreabilidade (TC-S2-01 a TC-S2-09)

| ID | Caso de Uso / Req | Cenário | Resultado esperado | Teste(s) |
| :--- | :--- | :--- | :--- | :--- |
| TC-S2-01 | UC04 / RF03, RF09 | Criação válida de lote de avaliação | Lote criado com status `em_processamento`, FK `user_id` correta; UC05 disparado | [`test_tc_s2_01_criacao_valida_de_lote`](../tests/domain/application/use_cases/test_submit_evaluation_batch.py#L48), [`test_tc_s2_01_criacao_valida_de_lote_via_api`](../tests/api/test_evaluation_batch_api.py#L64) |
| TC-S2-02 | UC04 / RF07 | Limite de upload excedido (A1) — 21 fotos | HTTP 400; `PhotoLimitExceededError` | [`test_tc_s2_02_limite_de_upload_excedido`](../tests/domain/application/use_cases/test_submit_evaluation_batch.py#L66), [`test_tc_s2_02_limite_de_upload_excedido_via_api`](../tests/api/test_evaluation_batch_api.py#L83) |
| TC-S2-03 | UC04 / RF07 | Submissão sem fotos (A2) | HTTP 400; `NoPhotosAttachedError` | [`test_tc_s2_03_submissao_sem_fotos`](../tests/domain/application/use_cases/test_submit_evaluation_batch.py#L77), [`test_tc_s2_03_submissao_sem_fotos_via_api`](../tests/api/test_evaluation_batch_api.py#L98) |
| TC-S2-04 | UC05 / RF06 | Detecção de jargão técnico via regex / `__tecnico__` | `classification_route = tecnico`; sem inferência emocional | [`test_tc_s2_04_jargao_tecnico_classifica_rota_tecnico`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L37) |
| TC-S2-05 | UC05 / RF04, RNF01 | Roteamento semântico Fast Track (SBERT) | `technical=False`, `used_fallback=False` → `classification_route = fast_track` | [`test_tc_s2_05_fast_track_sem_fallback`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L55) |
| TC-S2-06 | UC05 / RF05, RNF02 | Fallback via LLM em caso de ambiguidade | `used_fallback=True` → `classification_route = fallback` | [`test_tc_s2_06_fallback_via_llm_em_ambiguidade`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L74) |
| TC-S2-07 | UC05 / RF16 | Normalização de slug de âncora | `anchor_translator` normaliza case/espaços (`"Sublime"` → `"sublime"`) | [`test_tc_s2_07_normalizacao_de_slug_de_ancora`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L93) |
| TC-S2-08 | UC05 / RF16, RNF05 | Falha de mapeamento de âncora (A2) | Âncora desconhecida → fallback para `"global"`; fluxo não trava | [`test_tc_s2_08_falha_de_mapeamento_recai_sobre_global`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L109) |
| TC-S2-09 | UC05 / RNF06 | Indisponibilidade/timeout da API Photus B (A1) | `status = erro`; sem exceção propagada; API responde 201 mesmo assim | [`test_tc_s2_09_indisponibilidade_do_photus_b_marca_erro_sem_crash`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L126), [`test_photus_b_indisponivel_nao_propaga_excecao`](../tests/domain/application/use_cases/test_classify_semantic_anchor.py#L140), [`test_tc_s2_09_indisponibilidade_do_photus_b_nao_derruba_a_api`](../tests/api/test_evaluation_batch_api.py#L122) |

## Testes complementares (sem TC-S2 correspondente na spec original)

| Teste | O que cobre |
| :--- | :--- |
| [`test_limite_de_20_fotos_e_aceito`](../tests/domain/application/use_cases/test_submit_evaluation_batch.py#L86) | Limite exato de 20 fotos é o caso de borda aceito (só 21+ bloqueia) |
| [`test_submissao_sem_autenticacao_e_rejeitada`](../tests/api/test_evaluation_batch_api.py#L112) | `POST /batches` sem JWT → HTTP 401 |

## Validação end-to-end manual (fora da suíte automatizada)

Além dos testes acima, o fluxo completo foi validado com o `photus-uc` e o
`photus-b` reais rodando lado a lado (sem Docker, sem mocks):

- Jargão técnico (`f/1.8, ISO 100, 1/250s, 50mm`) → `classification_route =
  tecnico`, foto persistida em `uploads/{batch_id}/`.
- Input ambíguo → o fallback via Mistral do Photus B travou por ~15s antes
  de falhar internamente; o `HttpPhotusBClient` (timeout de 5s, valor da
  época do teste) expirou primeiro, `PhotusBUnavailableError` foi
  capturada e o lote foi marcado `status=erro` com HTTP 201 — confirmando
  TC-S2-09/RNF06 sob uma falha real, não simulada. Esse achado motivou o
  aumento do timeout padrão de `PHOTUS_B_TIMEOUT_SECONDS` de 5s para 15s,
  pra dar folga a uma chamada legítima ao Mistral (incluindo retry interno
  do litellm) sem descartar uma classificação que teria funcionado.

## Infraestrutura de teste

- `tests/fakes.py` — `FakeEvaluationBatchRepository`, `FakePhotoStorage`,
  `FakePhotusBClient`: implementações in-memory dos ports
  (`domain/application/interfaces/`), usadas nos testes unitários.
  `FakePhotusBClient` é configurável com um `SemanticClassification` fixo
  ou uma exceção fixa (para simular TC-S2-09).
- `tests/api/test_evaluation_batch_api.py` — sobrescreve
  `get_photus_b_client` (e `get_photo_storage`, via fixture `autouse`) da
  app real com `app.dependency_overrides`, reaproveitando a fixture
  `client` de `tests/api/conftest.py` (mesmo SQLite `:memory:` do Sprint 1).

## Não coberto nesta sprint

- UC06 (Avaliar Fotografias — Photus A/pré-processador C++) e, portanto,
  o preenchimento de `final_score`/`metrics_json`/`is_top3` em
  `EvaluatedPhoto` (Sprint 3).
- Retry/backoff na chamada ao Photus B — hoje é uma única tentativa com
  timeout fixo (RNF06 cobre resiliência, não retry).
- Processamento assíncrono/fila do UC05 — a classificação roda de forma
  síncrona dentro da mesma requisição de `POST /batches`.
- Testes de carga/performance (RNF fora do escopo funcional da Sprint 2).
