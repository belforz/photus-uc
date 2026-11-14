# Testes — MVP (Sprints 1 a 4)

Execução completa em 04/11/2026: **126/126** testes aprovados (116 sem binários + 10 de integração com os binários C++ reais).
Plano no molde do professor: `Plano_Testes_Photus_MVP.xlsx` (gerado por `xlsxgen/build_mvp.py`, a partir do JUnit da execução).

Rodar: `uv run pytest -q` (tudo) ou `uv run pytest -q -m "not integration"` (sem binários).

## Matriz de rastreabilidade (39 casos)

| ID | UC | Cenário | Suíte | Execução ao vivo / UI | Observação |
| :--- | :--- | :--- | :---: | :--- | :--- |
| TC-S1-01 | UC01 | Cadastro com sucesso de novo usuário | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-02 | UC01 | Validação de hash seguro na persistência | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-03 | UC01 | Cadastro com e-mail duplicado (A1) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-04 | UC01 | Submissão com campos obrigatórios vazios (A2) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-05 | UC02 | Autenticação com credenciais válidas | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-06 | UC02 | Autenticação com senha incorreta (A1) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-07 | UC02 | Autenticação com e-mail não existente (A2) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-08 | UC02 | Validação de token expirado ou inválido | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-09 | UC03 | Atualização de perfil do próprio usuário | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S1-10 | UC03 | Atualização de perfil para e-mail duplicado (A1) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S2-01 | UC04 | Criação válida de lote de avaliação | OK | Ao vivo (UI + HTTP), Sprint 2 |  |
| TC-S2-02 | UC04 | Limite de upload excedido (A1) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S2-03 | UC04 | Submissão sem fotos (A2) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S2-04 | UC05 | Detecção de jargão técnico via regex / `__tecnico__` | OK | Ao vivo (UI + HTTP), Sprint 2 |  |
| TC-S2-05 | UC05 | Roteamento semântico Fast Track (SBERT) | OK | Ao vivo (UI + HTTP), Sprint 2 |  |
| TC-S2-06 | UC05 | Fallback via LLM em caso de ambiguidade | OK | Suíte automatizada (execução manual: ver planilha do UC) | Mistral substituído por fake no teste automatizado (sem chamada externa). |
| TC-S2-07 | UC05 | Normalização de slug de âncora | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S2-08 | UC05 | Falha de mapeamento de âncora (A2) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S2-09 | UC05 | Indisponibilidade/Timeout da API Photus B (A1) | OK | Ao vivo (UI + HTTP), Sprint 2 |  |
| TC-S3-01 | UC06 | Execução e indexação pelo Pré-processador | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S3-02 | UC06 | Extração de features via OpenCV | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S3-03 | UC06 | Carregamento dinâmico de threshold JSON | OK | Ao vivo, binários C++ reais, 08/10/2026 | Spec cita thresholds_[ancora]_final.json; nome real é {ancora}_thresholds.json. |
| TC-S3-04 | UC06 | Fallback para threshold global (A1) | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S3-05 | UC06 | Aplicação de Hard-Rules e Random Forest | OK | Ao vivo, binários C++ reais, 08/10/2026 | Sem hard-rule de subexposição no engine; imagem preta cai por score do Random Forest. |
| TC-S3-06 | UC06 | Tratamento de faces em âncora Sublime | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S3-07 | UC06 | Persistência do resultado da avaliação | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S3-08 | UC06 | Desempenho de avaliação de lote completo | OK | Ao vivo, binários C++ reais, 08/10/2026 | Spec não fixa limite numérico; o teste adota 120 s (medido: 17,8 s para 20 fotos). |
| TC-S3-09 | UC06 | Falha na execução do binário C++ (A2) | OK | Ao vivo, binários C++ reais, 08/10/2026 |  |
| TC-S4-01 | UC07 | Consulta de histórico isolada por usuário | OK | UI real, 15/10/2026 |  |
| TC-S4-02 | UC07 | Histórico de usuário sem lotes (A1) | OK | UI real, 15/10/2026 |  |
| TC-S4-03 | UC08 | Visualização detalhada de lote concluído | OK | UI real, 15/10/2026 |  |
| TC-S4-04 | UC08 | Tentativa de acesso a lote de terceiro (A1) | OK | HTTP real, 15/10/2026 (tela 403 não verificada) | Spec aceita 403/404; implementado 403 (lote inexistente segue 404). |
| TC-S4-05 | UC08 | Consulta a lote ainda em processamento (A2) | OK | Suíte automatizada (execução manual: ver planilha do UC) | Auto-refresh de 3 s na UI implementado, não verificado no navegador. |
| TC-S4-06 | UC09 | Renderização do Top 3 para input no singular | OK | UI real, 15/10/2026 | Singular x plural é heurística lexical (a spec não define a regra). |
| TC-S4-07 | UC09 | Renderização para input no plural | OK | UI real, 15/10/2026 |  |
| TC-S4-08 | UC09 | Recorte Top 3 com menos de 3 fotos aprovadas (A1) | OK | Suíte automatizada (execução manual: ver planilha do UC) |  |
| TC-S4-09 | UC10 | Exclusão de lote com cascata | OK | UI real, 15/10/2026 |  |
| TC-S4-10 | UC10 | Tentativa de exclusão de lote de terceiro (A1) | OK | HTTP real, 15/10/2026 |  |
| TC-S4-11 | UC10 | Cancelamento de confirmação de exclusão (A2) | N/A (só front) | UI real, 15/10/2026 | Cancelar não chama a API: verificação só no front. |

## Correção na consolidação

- 401 intermitente em JWT válido (Sprint 4): causa reproduzida em teste (`iat` no futuro por relógio recuando → "not yet valid (iat)"); `JwtTokenService.decode` agora tem leeway de 10 s. Testes em `tests/infra/test_jwt_token_service.py`.

## Pendências conhecidas

- UI não verificada: tela 403 e auto-refresh de lote em processamento.
- Singular x plural (UC09) é heurística lexical; a spec não define a regra.
