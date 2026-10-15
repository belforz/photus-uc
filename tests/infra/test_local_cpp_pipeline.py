
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from domain.application.exceptions.evaluation_batch_exceptions import EvaluationEngineError
from domain.application.interfaces.photo_evaluation_pipeline import PhotoToEvaluate
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.pipeline.local_cpp_pipeline import (
    GLOBAL_THRESHOLDS_FILE,
    LocalCppPipeline,
    normalize_status,
)
from tests.infra._images import (
    write_black_png,
    write_flat_gradient_png,
    write_overexposed_png,
    write_underexposed_png,
)

SIBLINGS = Path(__file__).resolve().parents[3]
PRE_ROOT = SIBLINGS / "ai-pre-process-images"
PHOTUS_A_ROOT = SIBLINGS / "photus-a"
STAGING = SIBLINGS / "photus-system" / "data" / "uploads"
DATASET = SIBLINGS / "dataset" / "sublime" / "aprovadas"

_real_engine_available = (
    sys.platform.startswith("linux")
    and (PHOTUS_A_ROOT / "build" / "photus_a").is_file()
    and (PRE_ROOT / "scripts" / "run.sh").is_file()
    and (PRE_ROOT / "build" / "ai-preproccessor").is_file()
    and STAGING.parent.is_dir()
)
needs_real_engine = pytest.mark.skipif(
    not _real_engine_available, reason="binários C++ reais (photus-a / ai-pre-process-images) ausentes"
)


@pytest.fixture
def real_pipeline() -> LocalCppPipeline:
    return LocalCppPipeline(PRE_ROOT, PHOTUS_A_ROOT, STAGING, timeout_seconds=300)


def _dataset_photos(tmp_path: Path, n: int) -> list[PhotoToEvaluate]:
    candidates = sorted(DATASET.glob("*.jpg")) if DATASET.is_dir() else []
    if len(candidates) < n:
        pytest.skip(f"dataset local tem {len(candidates)} fotos; o teste precisa de {n}")
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    out = []
    for src in candidates[:n]:
        dst = uploads / src.name
        shutil.copy2(src, dst)
        out.append(PhotoToEvaluate(src.name, str(dst)))
    return out


def _synthetic(tmp_path: Path) -> list[PhotoToEvaluate]:
    uploads = tmp_path / "uploads"
    uploads.mkdir(exist_ok=True)
    dark = write_underexposed_png(uploads / "sintetica_subexposta.png")
    flat = write_flat_gradient_png(uploads / "sintetica_sem_bordas.png")
    return [PhotoToEvaluate(p.name, str(p)) for p in (dark, flat)]


def _no_leftover_staging(batch_id: str) -> bool:
    return not any(STAGING.glob(f"{batch_id}_*"))


# ---------------------------------------------------------------------------
# Engine real
# ---------------------------------------------------------------------------


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_01_preprocessador_indexa_e_categoriza_pela_ancora(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    fotos = _dataset_photos(tmp_path, 2)
    stage = real_pipeline._stage("tcs301", fotos)
    try:
        real_pipeline._preprocess(stage, "sublime")
        entries = real_pipeline._index_entries_for(stage)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    index = json.loads((PRE_ROOT / "local" / "images_index.json").read_text())
    assert index["category"] == "sublime"
    for foto in fotos:
        tipos = {e["type"] for e in entries if e["filename"] == foto.file_name}
        assert tipos == {"original", "color_gray", "color_hsv"}
    assert all(Path(e["path"]).is_file() for e in entries if e["type"] != "original")


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_02_opencv_extrai_as_features_no_payload_de_metricas(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    fotos = _dataset_photos(tmp_path, 2) + _synthetic(tmp_path)

    outcome = real_pipeline.run("tcs302", "sublime", fotos)

    assert {r.file_name for r in outcome.results} == {f.file_name for f in fotos}
    for resultado in outcome.results:
        assert resultado.status != PhotoEvaluationStatus.ERROR, resultado.details
        for chave in ("sharpness", "edge_density", "exposure_ratio"):
            assert isinstance(resultado.metrics[chave], (int, float)), chave
        assert resultado.face_metrics is not None
        assert 0.0 <= resultado.final_score <= 1.0
    assert _no_leftover_staging("tcs302")  # cópias de staging removidas


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_03_threshold_especifico_da_ancora_e_carregado_sem_recompilar(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    fotos = _dataset_photos(tmp_path, 1)

    outcome = real_pipeline.run("tcs303", "sublime", fotos)

    assert outcome.thresholds_source == "specific"
    assert outcome.thresholds_file == "sublime_thresholds.json"
    assert outcome.results[0].status != PhotoEvaluationStatus.ERROR


def test_tc_s3_03_resolve_thresholds_le_o_json_da_ancora_sem_binario(tmp_path: Path) -> None:
    root = tmp_path / "photus-a"
    vintage = root / "local" / "json" / "vintage_thresholds"
    vintage.mkdir(parents=True)
    (vintage / "vintage_thresholds.json").write_text("{}")
    pipeline = LocalCppPipeline(tmp_path / "pre", root, tmp_path / "stg")

    assert pipeline.resolve_thresholds("vintage") == ("vintage_thresholds.json", "specific")


@needs_real_engine
@pytest.mark.integration
@pytest.mark.parametrize("ancora", ["global", "ancora_sem_json_xyz"])
def test_tc_s3_04_ancora_sem_threshold_especifico_cai_no_global_sem_excecao(
    real_pipeline: LocalCppPipeline, tmp_path: Path, ancora: str
) -> None:
    fotos = _dataset_photos(tmp_path, 1)

    outcome = real_pipeline.run("tcs304", ancora, fotos)

    assert outcome.thresholds_source == "global"
    assert outcome.thresholds_file == GLOBAL_THRESHOLDS_FILE
    assert len(outcome.results) == 1
    assert outcome.results[0].status != PhotoEvaluationStatus.ERROR


@needs_real_engine
@pytest.mark.integration
@pytest.mark.parametrize(
    ("gerador", "regra"),
    [
        (write_flat_gradient_png, "Baixa informação detectada"),  # desfoque crítico
        (write_overexposed_png, "Exposição muito alta"),  # exposição extrema
    ],
)
def test_tc_s3_05_hard_rule_reprova_de_forma_terminal(
    real_pipeline: LocalCppPipeline, tmp_path: Path, gerador, regra: str
) -> None:
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    foto = gerador(uploads / "critica.png")

    outcome = real_pipeline.run("tcs305", "global", [PhotoToEvaluate("critica.png", str(foto))])

    (resultado,) = outcome.results
    assert resultado.status == PhotoEvaluationStatus.REJECTED
    assert regra in (resultado.details or "")  # a hard-rule nomeada foi a que terminou a cascata
    assert resultado.final_score <= 0.10  # MIN_SCORE: score travado pela hard-rule
    # Terminal: nenhuma exceção posterior (face metrics / ratio) foi aplicada por cima.
    assert "Face Metrics" not in resultado.details


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_05_subexposicao_pura_e_reprovada_pelo_score_e_nao_por_hard_rule_dedicada(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    preta = write_black_png(uploads / "preta.png")

    outcome = real_pipeline.run("tcs305b", "global", [PhotoToEvaluate("preta.png", str(preta))])

    (resultado,) = outcome.results
    assert resultado.status == PhotoEvaluationStatus.REJECTED
    assert resultado.final_score < 0.30
    assert resultado.metrics["exposure_ratio"] == 0.0
    assert "Exposição" not in (resultado.details or "")


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_06_ancora_sublime_tem_verificacao_facial_desativada_estruturalmente(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    sublime = json.loads(
        (PHOTUS_A_ROOT / "local/json/sublime_thresholds/sublime_thresholds.json").read_text()
    )
    # Estrutural: limites acima do máximo possível (1.0) => hasFace nunca é
    # verdadeiro e o ramo de rejeição por face nunca dispara.
    assert sublime["FACE_MIN_CONFIDENCE"] > 1.0
    assert sublime["FACE_AREA_RATIO_MAX"] > 1.0

    fotos = _dataset_photos(tmp_path, 2)
    outcome = real_pipeline.run("tcs306", "sublime", fotos)

    for resultado in outcome.results:
        assert "Face Metrics" not in (resultado.details or "")  # nenhuma exceção facial aplicada
        assert resultado.status != PhotoEvaluationStatus.ERROR


@needs_real_engine
@pytest.mark.integration
def test_tc_s3_08_desempenho_de_lote_completo_de_20_fotos(
    real_pipeline: LocalCppPipeline, tmp_path: Path
) -> None:
    fotos = _dataset_photos(tmp_path, 20)

    inicio = time.perf_counter()
    outcome = real_pipeline.run("tcs308", "sublime", fotos)
    duracao = time.perf_counter() - inicio

    print(f"\n[TC-S3-08] 20 fotos avaliadas em {duracao:.1f}s ({duracao / 20:.2f}s/foto)")
    assert len(outcome.results) == 20
    assert all(r.status != PhotoEvaluationStatus.ERROR for r in outcome.results)
    assert duracao < 120.0  # "demonstração interativa": o lote cheio fecha em < 2 min


# ---------------------------------------------------------------------------
# Árvore falsa: TC-S3-09 e mapeamento de status, com subprocess/exit code reais
# ---------------------------------------------------------------------------

_FAKE_PREPROCESSOR = """#!/bin/bash
dir="$2"
out="$(dirname "$0")/../local/images_index.json"
mkdir -p "$(dirname "$out")"
entries=""
for f in "$dir"/*; do
  n=$(basename "$f")
  entries="$entries{\\"filename\\":\\"$n\\",\\"path\\":\\"$f\\",\\"type\\":\\"original\\"},"
done
echo "{\\"images\\":[${entries%,}]}" > "$out"
%EXTRA%
"""


def _fake_tree(
    tmp_path: Path, photus_a_body: str, pre_extra: str = "", with_photus_a: bool = True
) -> LocalCppPipeline:
    pre = tmp_path / "pre"
    (pre / "scripts").mkdir(parents=True)
    run_sh = pre / "scripts" / "run.sh"
    run_sh.write_text(_FAKE_PREPROCESSOR.replace("%EXTRA%", pre_extra))
    run_sh.chmod(0o755)
    pa = tmp_path / "pa"
    (pa / "build").mkdir(parents=True)
    if with_photus_a:
        binary = pa / "build" / "photus_a"
        binary.write_text("#!/bin/bash\n" + photus_a_body)
        binary.chmod(0o755)
    return LocalCppPipeline(pre, pa, tmp_path / "stg", timeout_seconds=5)


def _one_photo(tmp_path: Path) -> list[PhotoToEvaluate]:
    f = tmp_path / "a.jpg"
    f.write_bytes(b"jpeg-fake")
    return [PhotoToEvaluate("a.jpg", str(f))]


linux_only = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="scripts bash")


@linux_only
def test_tc_s3_09_exit_code_de_erro_do_photus_a_vira_engine_error(tmp_path: Path) -> None:
    pipeline = _fake_tree(tmp_path, "exit 139\n")  # segfault, sem output.json

    with pytest.raises(EvaluationEngineError, match="exit=139"):
        pipeline.run("b1", "sublime", _one_photo(tmp_path))

    assert not any((tmp_path / "stg").glob("b1_*"))  # staging limpo mesmo na falha


@linux_only
def test_tc_s3_09_erro_com_output_parcial_preserva_o_que_foi_avaliado(tmp_path: Path) -> None:
    body = (
        'cat > "$3" <<EOF\n'
        '{"results":[{"filename":"a.jpg","status":"Aprovado","final_score":0.8,"metrics":{}},'
        '{"status":"error","details":"x"}],"error":"boom"}\nEOF\nexit 1\n'
    )
    pipeline = _fake_tree(tmp_path, body)

    with pytest.raises(EvaluationEngineError) as erro:
        pipeline.run("b1", "sublime", _one_photo(tmp_path))

    assert [r.file_name for r in erro.value.partial_results] == ["a.jpg"]
    assert erro.value.partial_results[0].status == PhotoEvaluationStatus.APPROVED


@linux_only
def test_tc_s3_09_preprocessador_com_exit_code_de_erro(tmp_path: Path) -> None:
    pipeline = _fake_tree(tmp_path, "exit 0\n", pre_extra="echo falhou >&2\nexit 3")

    with pytest.raises(EvaluationEngineError, match="Pré-processador terminou com exit=3"):
        pipeline.run("b1", "sublime", _one_photo(tmp_path))


@linux_only
def test_tc_s3_09_timeout_do_binario_vira_engine_error(tmp_path: Path) -> None:
    pipeline = _fake_tree(tmp_path, "sleep 30\n")
    pipeline._timeout_seconds = 0.5

    with pytest.raises(EvaluationEngineError, match="timeout"):
        pipeline.run("b1", "sublime", _one_photo(tmp_path))


@linux_only
def test_tc_s3_09_binario_ausente_vira_engine_error(tmp_path: Path) -> None:
    pipeline = _fake_tree(tmp_path, "exit 0\n", with_photus_a=False)

    with pytest.raises(EvaluationEngineError, match="não encontrado"):
        pipeline.run("b1", "sublime", _one_photo(tmp_path))


@linux_only
def test_quatro_status_do_engine_mapeiam_para_o_enum_e_erro_por_foto_nao_derruba_o_lote(
    tmp_path: Path,
) -> None:
    body = (
        'cat > "$3" <<EOF\n'
        '{"results":['
        '{"filename":"a.jpg","status":"Aprovado","final_score":0.9,"metrics":{"sharpness":1.0}},'
        '{"filename":"b.jpg","status":"Indefinido","final_score":0.4,"metrics":{}},'
        '{"filename":"c.jpg","status":"Reprovado","final_score":0.1,"metrics":{}},'
        '{"filename":"d.jpg","status":"Revisao_Humana","final_score":0.5,"metrics":{}},'
        '{"filename":"e.jpg","status":"error","details":"Falha ao carregar a imagem"}'
        ']}\nEOF\nexit 0\n'
    )
    pipeline = _fake_tree(tmp_path, body)
    fotos = []
    for nome in "abcde":
        f = tmp_path / f"{nome}.jpg"
        f.write_bytes(b"x")
        fotos.append(PhotoToEvaluate(f.name, str(f)))

    outcome = pipeline.run("b1", "global", fotos)

    assert [r.status for r in outcome.results] == [
        PhotoEvaluationStatus.APPROVED,
        PhotoEvaluationStatus.UNDEFINED,
        PhotoEvaluationStatus.REJECTED,
        PhotoEvaluationStatus.HUMAN_REVIEW,
        PhotoEvaluationStatus.ERROR,
    ]
    assert outcome.results[4].final_score is None
    assert "Falha ao carregar" in outcome.results[4].details


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        ("Aprovado", PhotoEvaluationStatus.APPROVED),
        ("Revisao_Humana", PhotoEvaluationStatus.HUMAN_REVIEW),
        ("Revisão Humana", PhotoEvaluationStatus.HUMAN_REVIEW),
        ("INDEFINIDO", PhotoEvaluationStatus.UNDEFINED),
        ("coisa-nova", None),
        (None, None),
    ],
)
def test_normalize_status(bruto: str | None, esperado: PhotoEvaluationStatus | None) -> None:
    assert normalize_status(bruto) == esperado
