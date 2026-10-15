# Docker — stack do backend (branch `release/eg-software`)

Quatro containers, três imagens de aplicação:

```
                         ┌────────────┐   POST /v1/categorize   ┌──────────┐
 front ──:8000──►  app-web (photus-uc) ───────────────────────►  │ photus-b │  SBERT (torch CPU)
                         │  │                                     └──────────┘
                         │  └── POST /v1/evaluate ──────────────► ┌───────────────┐
                         ▼                                         │ photus-engine │ ai-preproccessor + photus_a
                        db (postgres)                              └───────────────┘
```

O `photus-uc` **não constrói nem embute** o Photus B e o engine: consome as imagens deles como
dependências de runtime, por HTTP, na rede interna do compose (`http://photus-b:8000`,
`http://photus-engine:8000`). Só o `app-web` (8000) e o `db` (5432) publicam porta.

## Subir

Imagens no Docker Hub, usuário `belforzz` (`PHOTUS_REGISTRY`/`PHOTUS_TAG`, default `belforzz` / `latest`; para
travar uma versão use `PHOTUS_TAG=v0.0.0`):

```bash
docker compose pull
docker compose up -d
```

Construindo localmente (repos irmãos em `../photus-b`, `../photus-engine`, `../photus-a`, `../ai-pre-process-images`):

```bash
(cd ../photus-engine && ./scripts/prepare_context.sh)      # monta o contexto do engine, inclui o modelo RF
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

Convenção de tags (a mesma do `photus-system`): `vX.Y.Z` imutável por release + `latest` sempre apontando
para a última. Publicação (`belforzz/photus-b`, `belforzz/photus-engine`, `belforzz/photus-uc`):

```bash
docker build -t belforzz/photus-b:v0.0.0 -t belforzz/photus-b:latest .
docker push belforzz/photus-b:v0.0.0 && docker push belforzz/photus-b:latest
```

O `app-web` só inicia depois que `db`, `photus-b` e `photus-engine` estão *healthy*. O Photus B leva ~1 min
(carrega o transformer no `lifespan`); isso é coberto pelo `start_period` do healthcheck.

### Variáveis (`.env` desta pasta, todas opcionais)

| Variável | Para quê |
| :--- | :--- |
| `PHOTUS_REGISTRY`, `PHOTUS_TAG` | origem das imagens |
| `MISTRAL_API_KEY`, `HF_API_KEY`, `LLM_VALID_MODELS`, `LLM_*` | segredos do Photus B — **entram só em runtime, nunca na imagem**. Sem `MISTRAL_API_KEY` o fallback LLM fica desligado |
| `POSTGRES_USER/PASSWORD/DB` | banco |
| `PHOTUS_B_MEM_LIMIT` (3g), `PHOTUS_ENGINE_MEM_LIMIT` (2g), `PHOTUS_B_THREADS` (2) | limites de recurso |

O `PIPELINE_BACKEND=http` e as URLs dos serviços são fixados no compose. Fora do Docker, o `photus-uc`
continua rodando em modo `local` (`PIPELINE_BACKEND=local`, default): subprocess dos binários C++.

## As imagens

| Imagem | Origem | Tamanho (disco / comprimido) | Notas |
| :--- | :--- | :--- | :--- |
| `photus-uc` | `photus-uc/Dockerfile` | 308 MB | sem mudança de arquitetura; `uploads` virou volume |
| `photus-b` | `photus-b/Dockerfile` | 3,75 GB / 1,04 GB | torch **CPU** (o `uv.lock` resolve CUDA, ~3 GB a mais); pesos do MiniLM baixados no build, runtime `HF_HUB_OFFLINE=1` |
| `photus-engine` | `photus-engine/Dockerfile` | 1,03 GB / 246 MB | compila os 2 binários em multi-stage; runtime só com as libs apt de fato usadas |

O Photus B continua pesado: pandas, matplotlib, seaborn, scipy e spaCy estão no `pyproject.toml` e entram
no venv. Se o tamanho incomodar, o próximo passo é mover o que só os notebooks/scripts usam para um
grupo `dev` (afeta o `uv.lock` do `photus-b`, por isso não foi mexido aqui).

## Validação real (2026-10-14, Docker Desktop, 4 CPUs / 7,6 GiB)

Stack completo, Postgres de verdade, fotos reais (`dataset/sublime/aprovadas`), via `curl` + `GET /batches/{id}`:

| Cenário | Resultado |
| :--- | :--- |
| Texto sublime, 5 fotos | `concluido`, 5/5 aprovadas, `sublime_thresholds.json`; 1º lote (frio) 32 s |
| Jargão técnico, 3 fotos | âncora `tecnico` → `thresholds_global.json`, `concluido` em ~6 s (morno) |
| Container `photus-engine` parado, 2 fotos | `POST` 201; lote `erro` em ~2 s; `/health` do app segue `ok` (A2) |
| Scores vs. binário local (WSL) | **idênticos** (ex.: 0,5987866520881653), apesar de Release + Debian vs. build padrão + Ubuntu |

Memória em regime (`docker stats`): `photus-b` **1,79 GiB** (por isso o limite padrão é 3g), `photus-engine` 258 MiB,
`app-web` 150 MiB, `db` 42 MiB. O pico do engine num lote de 20 fotos de ~5 MB não foi medido.

## Riscos conhecidos

- **Modelo RF fora do git.** `photus-a/local/technician_model/**/*.xml` (~100 MB) é gitignored. O engine só
  constrói a partir do working tree local (`prepare_context.sh`). Para CI/registry: Git LFS ou release asset.
- **`prepare_context.sh` usa o working tree** de `../photus-a` (hoje na branch `fix/photus-a`, com
  `JudgeRules.cpp` modificado). Confira a branch/commit antes de publicar uma imagem.
- **Primeira requisição lenta.** O 1º `POST /batches` após o start paga o aquecimento do Photus B.
- **Um lote por vez no engine.** Vários usuários simultâneos enfileiram no lock; o `app-web` aguarda até
  `PHOTUS_ENGINE_TIMEOUT_SECONDS` (600 s). Escalar exige fila, não mais réplicas.
- O `UC05` continua síncrono dentro do `POST /batches` (latência do Photus B aparece na resposta).
