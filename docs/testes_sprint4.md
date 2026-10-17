# Sprint 4 — Histórico, Resultados, Top 3 e Exclusão (UC07–UC10)

Backend em `photus-uc`; front em `photus-system` (`ui/history.py`, `ui/results.py`).

## Endpoints novos / alterados

| Método | Rota | Caso de uso | Resposta |
| :-- | :-- | :-- | :-- |
| GET | `/batches` | UC07 | 200 `[BatchSummary]` do mais recente ao mais antigo (`[]` se não há lotes) |
| GET | `/batches/{id}` | UC08/UC09 | 200 detalhe (**novo:** `is_singular`; `is_top3` agora é preenchido); 403 se o lote é de outro usuário; 404 se não existe |
| GET | `/batches/{id}/photos/{photo_id}/image` | UC08 | arquivo da foto, só para o proprietário (403/404) |
| DELETE | `/batches/{id}` | UC10 | 204; remove lote + fotos avaliadas + arquivos enviados; 403/404 |

Mudança de comportamento: antes, lote de outro usuário respondia **404**; agora **403** (RF14, tela 403 do Figma). Lote inexistente segue 404.

## Decisões / divergências da spec

- **Singular vs. plural (UC09)** não tinha fonte na spec. Foi implementado em `domain/application/services/phrase_number.py`, heurística lexical em português (primeiro marcador de número decide: `a melhor foto das montanhas` = singular; `fotos do ensaio` = plural; sem marcador, singular). Não há NLP: frases ambíguas caem em singular (pior caso: Top 3 destacado acima da galeria completa).
- **Top 3** é calculado no fim do UC06 (`mark_top3` em `evaluate_photos.py`): só fotos `aprovado`, maior `final_score`, desempate por nome de arquivo, no máximo 3; só se a frase for singular. Menos de 3 aprovadas → marca só as disponíveis (A1). `revisao_humana`/`indefinido` nunca entram.
- Lotes concluídos **antes** da Sprint 4 têm `is_top3 = false` (não são recalculados).
- Cascata (RF13) é explícita no repositório (apaga `evaluated_photo` e depois `evaluation_batch`), sem depender de `PRAGMA foreign_keys` no SQLite; os arquivos em `uploads/{batch_id}` também são removidos.
- Excluir um lote ainda `em_processamento` é permitido (um lote preso após queda do servidor não ficaria indeletável); o job em background falha sem efeito colateral e é logado.
- Sem migration: nenhuma coluna nova (`is_singular` é derivado do texto).

## Mapa dos casos de teste

| ID | Onde |
| :-- | :-- |
| TC-S4-01 | `tests/api/test_sprint4_api.py::test_tc_s4_01_historico_isolado_por_usuario` |
| TC-S4-02 | `…::test_tc_s4_02_usuario_sem_lotes_recebe_lista_vazia` + estado vazio na UI |
| TC-S4-03 | `…::test_tc_s4_03_detalhe_de_lote_concluido_traz_fotos_scores_e_metricas` |
| TC-S4-04 | `…::test_tc_s4_04_acesso_a_lote_de_terceiro_e_negado_com_403`; `test_uc06_api.py::test_get_lote_de_outro_usuario_retorna_403` |
| TC-S4-05 | `…::test_tc_s4_05_lote_em_processamento_responde_status_parcial` (UI: aviso + timer de 3 s) |
| TC-S4-06 | `…::test_tc_s4_06_singular_expoe_is_singular_e_marca_top3`; `test_top3.py` |
| TC-S4-07 | `…::test_tc_s4_07_plural_nao_marca_top3`; `test_top3.py` |
| TC-S4-08 | `…::test_tc_s4_08_menos_de_3_aprovadas_destaca_so_as_disponiveis`; `test_top3.py` |
| TC-S4-09 | `…::test_tc_s4_09_exclusao_remove_lote_fotos_e_arquivos` |
| TC-S4-10 | `…::test_tc_s4_10_exclusao_de_lote_de_terceiro_retorna_403_e_preserva_dados` |
| TC-S4-11 | só front (cancelar não chama a API) — verificado manualmente no navegador |

Mais: `tests/domain/application/services/test_phrase_number.py` (17 frases singular/plural).

## Verificação real (2026-10-15)

photus-b + photus-uc (binários C++ reais) + photus-system, dados semeados por HTTP, UI no navegador:
histórico isolado por usuário; resultado singular (Top 3 + galeria, `revisao_humana` fora do Top 3) e plural (só galeria); filtro por status; gaveta de métricas; cancelar/confirmar exclusão (banco e `uploads/` limpos, lote de outro usuário intacto); 403 real via HTTP em GET e DELETE; estado vazio; troca de sessão (logout/login) volta à Nova Avaliação sem vazar o histórico anterior.

Não verificado na UI: tela 403 e o auto-refresh de lote `em_processamento` (cobertos só pelos testes de API e por leitura do código).
