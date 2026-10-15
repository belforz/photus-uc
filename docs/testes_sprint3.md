# Testes — Sprint 3 (Pré-processamento e Avaliação Técnica — Photus A)

Cobre UC06 (Avaliar Fotografias) e a matriz TC-S3-01 a TC-S3-09. 40 testes
novos (78 no total da suíte), em três níveis:

- **Unitários** (`tests/domain/application/use_cases/test_evaluate_photos.py`)
  — o use case `EvaluatePhotos` com repositório e pipeline fake (in-memory).
- **Integração HTTP** (`tests/api/test_uc06_api.py`) — a app FastAPI com
  `TestClient` + SQLite em memória, o job real `SessionEvaluationJob` e um
  pipeline fake. O `TestClient` executa as `BackgroundTasks` antes de
  devolver a resposta, então o `GET /batches/{id}` seguinte já vê o estado final.
- **Infra / binários reais** (`tests/infra/test_local_cpp_pipeline.py`) —
  `LocalCppPipeline` executando os binários C++ **de verdade**
  (`ai-preproccessor` e `photus_a`), sem mocks, marcados `@pytest.mark.integration`
  e pulados automaticamente se os binários/dataset não existirem. O TC-S3-09
  usa uma árvore de diretórios com scripts shell no lugar dos binários, para
  exercitar `subprocess`/exit code/timeout reais de forma determinística.

Rodar tudo: `uv run pytest -q` (~50 s, por causa dos binários). Sem os
binários C++: `uv run pytest -q -m "not integration"`.

## O que foi implementado

| Peça | Onde |
| :--- | :--- |
| Use case UC06 | `domain/application/use_cases/evaluate_photos.py` |
| Consulta (Monitor + Diagnóstico) | `domain/application/use_cases/get_evaluation_batch.py` → `GET /batches/{id}` |
| Port do engine | `domain/application/interfaces/photo_evaluation_pipeline.py` |
| Adapter (pré-processador → Photus A) | `infra/pipeline/local_cpp_pipeline.py` |
| Job em background (sessão própria, nunca deixa o lote preso) | `infra/jobs/evaluation_job.py` |
| Novos estados | `BatchStatus.COMPLETED` (`concluido`); `PhotoEvaluationStatus.UNDEFINED/HUMAN_REVIEW/ERROR` |
| Config | `PREPROCESSOR_ROOT`, `PHOTUS_A_ROOT`, `PIPELINE_STAGING_DIR`, `PIPELINE_TIMEOUT_SECONDS` (`infra/config.py`) |

Sem migração Alembic: as colunas `final_score`/`metrics_json`/`is_top3` já
existiam desde a Sprint 2 e os novos status são apenas strings.

**Fluxo.** `POST /batches` (UC04 + UC05) continua devolvendo `201` rápido com
`status = em_processamento`. Se a âncora foi classificada, o UC06 é agendado
como `BackgroundTask` e o front acompanha por `GET /batches/{id}`
(`em_processamento → concluido | erro`, mais `evaluated_photos / total_photos`
para o "Avaliando foto X de N" do Monitor).

## Matriz de rastreabilidade (TC-S3-01 a TC-S3-09)

| ID | Caso de Uso / Req | Cenário | Resultado esperado | Teste(s) |
| :--- | :--- | :--- | :--- | :--- |
| TC-S3-01 | UC06 / RF15 | Execução e indexação pelo Pré-processador | Índice com original + `color_gray` + `color_hsv` por foto, categoria = âncora | [`test_tc_s3_01_preprocessador_indexa_e_categoriza_pela_ancora`](../tests/infra/test_local_cpp_pipeline.py#L95) |
| TC-S3-02 | UC06 / RF07 | Extração de features via OpenCV | `sharpness`, `edge_density`, `exposure_ratio` (+ `face_metrics`) no payload | [`test_tc_s3_02_opencv_extrai_as_features_no_payload_de_metricas`](../tests/infra/test_local_cpp_pipeline.py#L116) |
| TC-S3-03 | UC06 / RNF04 | Threshold JSON carregado dinamicamente | `sublime_thresholds.json` usado sem recompilar; arquivo registrado no `metrics_json` | [`…threshold_especifico_da_ancora_e_carregado_sem_recompilar`](../tests/infra/test_local_cpp_pipeline.py#L135), [`…resolve_thresholds_le_o_json_da_ancora_sem_binario`](../tests/infra/test_local_cpp_pipeline.py#L147), [`test_tc_s3_03_registra_o_arquivo_de_threshold_especifico_usado`](../tests/domain/application/use_cases/test_evaluate_photos.py#L128) |
| TC-S3-04 | UC06 / RF16, RNF05 | Fallback para threshold global (A1) | `thresholds_global.json`, avaliação completa, sem exceção | [`…ancora_sem_threshold_especifico_cai_no_global_sem_excecao`](../tests/infra/test_local_cpp_pipeline.py#L160) (2 âncoras), [`test_tc_s3_04_ancora_sem_threshold_especifico_usa_global_sem_interromper`](../tests/domain/application/use_cases/test_evaluate_photos.py#L142) |
| TC-S3-05 | UC06 / RF08, RF10 | Hard-rule terminal | `Reprovado`, score travado em `MIN_SCORE`, motivo no `details`, sem regras posteriores | [`test_tc_s3_05_hard_rule_reprova_de_forma_terminal`](../tests/infra/test_local_cpp_pipeline.py#L182) (2 hard-rules), [`…subexposicao_pura_e_reprovada_pelo_score…`](../tests/infra/test_local_cpp_pipeline.py#L201), [`test_tc_s3_05_reprovacao_por_hard_rule_e_persistida_com_o_motivo`](../tests/domain/application/use_cases/test_evaluate_photos.py#L160) |
| TC-S3-06 | UC06 / Regra de negócio | Faces sob âncora Sublime | Verificação facial desativada estruturalmente; nenhuma exceção facial aplicada | [`test_tc_s3_06_ancora_sublime_tem_verificacao_facial_desativada_estruturalmente`](../tests/infra/test_local_cpp_pipeline.py#L224) |
| TC-S3-07 | UC06 / RF10, RF09 | Persistência do resultado | 5 fotos → 5 registros com `score_final`, `status_avaliacao`, `metricas_json`; lote `concluido` | [`test_tc_s3_07_persiste_um_registro_por_foto_e_conclui_o_lote`](../tests/domain/application/use_cases/test_evaluate_photos.py#L84), [`test_tc_s3_07_lote_de_5_fotos_persiste_5_avaliacoes_e_conclui`](../tests/api/test_uc06_api.py#L85) |
| TC-S3-08 | UC06 / RNF07 | Desempenho — lote de 20 fotos | Tempo aceitável p/ demo interativa | [`test_tc_s3_08_desempenho_de_lote_completo_de_20_fotos`](../tests/infra/test_local_cpp_pipeline.py#L245) |
| TC-S3-09 | UC06 / Subprocesso | Falha do binário (A2) | Lote `erro`, fotos já avaliadas preservadas, servidor de pé | [`…exit_code_de_erro_do_photus_a…`](../tests/infra/test_local_cpp_pipeline.py#L305), [`…erro_com_output_parcial…`](../tests/infra/test_local_cpp_pipeline.py#L315), [`…preprocessador_com_exit_code_de_erro`](../tests/infra/test_local_cpp_pipeline.py#L331), [`…timeout_do_binario…`](../tests/infra/test_local_cpp_pipeline.py#L339), [`…binario_ausente…`](../tests/infra/test_local_cpp_pipeline.py#L348), [`test_tc_s3_09_falha_do_binario_marca_lote_erro_sem_propagar_excecao`](../tests/domain/application/use_cases/test_evaluate_photos.py#L182), [`test_tc_s3_09_falha_do_engine_marca_lote_erro_e_a_api_continua_de_pe`](../tests/api/test_uc06_api.py#L112) |

## Testes complementares (sem TC-S3 correspondente na spec)

| Teste | O que cobre |
| :--- | :--- |
| `test_quatro_status_do_engine_mapeiam_para_o_enum_e_erro_por_foto_nao_derruba_o_lote` | `Aprovado/Indefinido/Reprovado/Revisao_Humana/error` → enum; falha numa foto não derruba o lote |
| `test_normalize_status` | `Revisao_Humana` (sem acento, como o C++ emite) e `Revisão Humana` → `HUMAN_REVIEW` |
| `test_foto_sem_resultado_do_engine_vira_erro_e_o_lote_conclui` | Foto que o pré-processador descartou: registro preservado com `erro` |
| `test_precondicao_lote_sem_ancora_classificada_e_rejeitado` | Pré-condição do UC06 |
| `test_uc05_com_photus_b_fora_nao_dispara_avaliacao_tecnica` | Photus B fora → lote `erro` e **nenhuma** chamada ao engine |
| `test_excecao_inesperada_no_job_nao_deixa_o_lote_preso_em_processamento` | Última barreira do job |
| `test_get_lote_de_outro_usuario_retorna_404` / `…inexistente…` / `…sem_autenticacao…` | Autorização do `GET /batches/{id}` |

## Validação end-to-end real (2026-10-08)

Com `photus-b` (:8000) e `photus-uc` (:8001) reais, os binários C++ reais e 5
fotos reais do dataset (`dataset/sublime/aprovadas`, ~5,5 MB cada), via HTTP
(`curl` multipart + `GET /batches/{id}`):

| Cenário | Resultado observado |
| :--- | :--- |
| Texto "…paisagens amplas, com céu e horizonte… sublime" (5 fotos) | `POST` 0,75 s → `em_processamento`, âncora `sublime`, rota `fast_track`; ~8 s depois `concluido`, 5/5 avaliadas (todas `aprovado`, scores 0,595–0,798), `thresholds_file = sublime_thresholds.json` (**TC-S3-01/02/03/07**) |
| Texto técnico "f/1.8, ISO 100, 1/250s, 50mm" (3 fotos) | âncora `tecnico`, rota `tecnico` → sem `tecnico_thresholds.json` → `thresholds_file = thresholds_global.json`, `concluido`, sem exceção (**TC-S3-04 / A1**) |
| Segundo `photus-uc` com `PHOTUS_A_ROOT=/nonexistent/photus-a` (3 fotos) | `POST` 201; ~2 s depois lote `erro`, 3 fotos `pendente`, `/health` segue `ok` (**TC-S3-09 / A2**) |

**TC-S3-08 (medido):** 20 fotos reais (~111 MB) em **17,8 s** de ponta a ponta
(≈ 0,89 s/foto) — pré-processamento + Photus A, com o lock global. A spec não
define o limite numérico; o teste adota 120 s como teto.

## Divergências entre a spec e o comportamento real do engine

Achados ao rodar os binários de verdade — documentados em vez de forçados:

1. **Nome do arquivo de threshold.** A spec fala em `thresholds_[ancora]_final.json`;
   o Photus A carrega `local/json/{ancora}_thresholds/{ancora}_thresholds.json`
   e cai em `local/json/thresholds_global.json`. O adapter detecta qual dos dois
   será usado. A âncora de exemplo da spec ("Vintage") não existe no vocabulário
   do sistema (as 10 estéticas + `tecnico`); os testes usam `sublime`.
2. **"Severa subexposição" não é hard-rule.** `exposure_ratio` mede
   *superexposição* (imagem branca = 1.0, preta = 0.0). As hard-rules reais são
   exposição estourada (`Exposição muito alta`) e baixa informação/desfoque crítico
   (`Baixa informação detectada`). Uma imagem totalmente preta é `Reprovado` mas
   pelo score do Random Forest (< 0,30), não por hard-rule dedicada. O resultado
   final do TC-S3-05 (Reprovado) bate; o mecanismo descrito na spec, não.
3. **Status do engine sem acento.** O C++ emite `Revisao_Humana`; o adapter
   normaliza para `revisao_humana`. Os status são persistidos em slug minúsculo
   (`aprovado`/`indefinido`/`reprovado`/`revisao_humana`), igual aos já existentes
   (`pendente`, `em_processamento`); o front mapeia para os rótulos da spec.
4. **Status extra `erro` por foto.** Não está nos 4 da spec, mas o Figma da
   Sprint 3 pede o card "Erro ao processar imagem. Registro preservado.".
5. **Progresso granular não existe.** O Photus A roda uma vez para o lote; o
   progresso vai de `0/N` para `N/N`, não incrementa foto a foto.
6. **A2 "preservando fotos já avaliadas".** Só há o que preservar se o binário
   gravar um `output.json` parcial antes de falhar; um crash duro (segfault) não
   deixa nada.

## Pontos de integração (risco operacional)

- **Allowlist hardcoded do pré-processador.** `pathsUtils.cpp::isValidPath` só
  aceita imagens sob `/home/belforz/photus-system/data/uploads/`. Por isso o
  adapter **copia** as fotos para uma pasta de staging nessa árvore
  (`PIPELINE_STAGING_DIR`, derivada do repo irmão por padrão) e remove a cópia
  no fim — inclusive em caso de falha. Mover os repos exige ajustar o C++.
- **`images_index.json` é global e cumulativo** (já passa de 45 mil linhas) e
  `images/temp/color_spaces/` é compartilhada. Dois lotes simultâneos
  corromperiam um ao outro, então a execução é serializada por um lock **por
  processo** — rode **um** worker uvicorn.
- **`scripts/run.sh` devolve o exit code só da última imagem.** Uma falha no meio
  do lote não aparece no exit code; a foto some do índice e vira `erro`.
- **Docker.** Os binários C++ precisam estar na imagem do `photus-uc` (ou
  montados) para o UC06 rodar em container; sem eles o lote termina em `erro`
  (A2), sem derrubar a API.

## Não coberto nesta sprint

- Seleção do Top 3 (`is_top3`) e histórico — Sprint 4.
- Fila/worker dedicado: o UC06 usa `BackgroundTasks` do FastAPI (se o processo
  morrer no meio, o lote fica `em_processamento`; não há reprocessamento).
- Front da Sprint 3 (Monitor / Diagnóstico por Foto) — consome `GET /batches/{id}`.
