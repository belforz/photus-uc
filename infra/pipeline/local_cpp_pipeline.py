from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path

from domain.application.exceptions.evaluation_batch_exceptions import EvaluationEngineError
from domain.application.interfaces.photo_evaluation_pipeline import (
    PhotoEvaluationPipeline,
    PhotoEvaluationResult,
    PhotoToEvaluate,
    PipelineOutcome,
)
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.pipeline.status_mapping import build_result, normalize_status  # noqa: F401

logger = logging.getLogger(__name__)

GLOBAL_THRESHOLDS_FILE = "thresholds_global.json"
_SAFE_ANCHOR = re.compile(r"^[a-z0-9_]+$")
_VARIANTS_USED_BY_PHOTUS_A = ("color_gray", "color_hsv")

class LocalCppPipeline(PhotoEvaluationPipeline):
    _PIPELINE_LOCK = threading.Lock()

    def __init__(
        self,
        preprocessor_root: str | Path,
        photus_a_root: str | Path,
        staging_dir: str | Path,
        timeout_seconds: float = 300.0,
    ) -> None:
        self._preprocessor_root = Path(preprocessor_root).resolve()
        self._photus_a_root = Path(photus_a_root).resolve()
        self._staging_dir = Path(staging_dir).resolve()
        self._timeout_seconds = timeout_seconds
        self._preprocessor_script = self._preprocessor_root / "scripts" / "run.sh"
        self._photus_a_bin = self._photus_a_root / "build" / "photus_a"
        self._images_index = self._preprocessor_root / "local" / "images_index.json"


    def run(
        self, batch_id: str, anchor: str, photos: list[PhotoToEvaluate]
    ) -> PipelineOutcome:
        safe_anchor = anchor if _SAFE_ANCHOR.match(anchor or "") else "global"
        thresholds_file, thresholds_source = self.resolve_thresholds(safe_anchor)

        with self._PIPELINE_LOCK:
            stage_dir = self._stage(batch_id, photos)
            try:
                self._preprocess(stage_dir, safe_anchor)
                entries = self._index_entries_for(stage_dir)
                results = self._run_photus_a(entries, safe_anchor)
            finally:
                shutil.rmtree(stage_dir, ignore_errors=True)

        return PipelineOutcome(
            results=results,
            thresholds_file=thresholds_file,
            thresholds_source=thresholds_source,
        )

    def resolve_thresholds(self, anchor: str) -> tuple[str, str]:
        specific = (
            self._photus_a_root / "local" / "json" / f"{anchor}_thresholds" / f"{anchor}_thresholds.json"
        )
        if specific.is_file():
            return f"{anchor}_thresholds.json", "specific"
        return GLOBAL_THRESHOLDS_FILE, "global"


    def _stage(self, batch_id: str, photos: list[PhotoToEvaluate]) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        stage_dir = self._staging_dir / f"{batch_id}_{stamp}"
        stage_dir.mkdir(parents=True, exist_ok=True)
        for photo in photos:
            source = Path(photo.file_path)
            if not source.is_file():
                logger.warning("Foto %s não existe em disco; pulando no staging.", source)
                continue
            shutil.copy2(source, stage_dir / photo.file_name)
        return stage_dir

    def _preprocess(self, stage_dir: Path, anchor: str) -> None:
        if not self._preprocessor_script.is_file():
            raise EvaluationEngineError(
                f"Pré-processador não encontrado em {self._preprocessor_script}."
            )
        proc = self._run(
            ["bash", str(self._preprocessor_script), "--dir", str(stage_dir), "--category", anchor],
            cwd=self._preprocessor_root,
            what="pré-processador",
        )
        if proc.returncode != 0:
            raise EvaluationEngineError(
                f"Pré-processador terminou com exit={proc.returncode}: "
                f"{(proc.stderr or proc.stdout)[-1000:]}"
            )

    def _index_entries_for(self, stage_dir: Path) -> list[dict]:
        if not self._images_index.is_file():
            raise EvaluationEngineError(
                f"images_index.json não encontrado em {self._images_index}."
            )
        try:
            index = json.loads(self._images_index.read_text())
        except json.JSONDecodeError as exc:
            raise EvaluationEngineError(f"images_index.json ilegível: {exc}") from exc

        stage_prefix = str(stage_dir) + "/"
        originals = [
            img
            for img in index.get("images", [])
            if img.get("type") == "original"
            and str(Path(img.get("path", "")).resolve()).startswith(stage_prefix)
        ]
        if not originals:
            raise EvaluationEngineError(
                "Pré-processador não indexou nenhuma fotografia deste lote."
            )

        names = {o["filename"] for o in originals}
        latest_variant: dict[tuple[str, str], dict] = {}
        for img in index.get("images", []):
            if img.get("type") in _VARIANTS_USED_BY_PHOTUS_A and img.get("filename") in names:
                latest_variant[(img["filename"], img["type"])] = img
        return originals + list(latest_variant.values())

    def _run_photus_a(self, entries: list[dict], anchor: str) -> list[PhotoEvaluationResult]:
        if not self._photus_a_bin.is_file():
            raise EvaluationEngineError(
                f"Binário do Photus A não encontrado em {self._photus_a_bin}."
            )
        with tempfile.TemporaryDirectory(prefix="photus_a_run_") as tmp:
            tmp_path = Path(tmp)
            index_file = tmp_path / "image_index.json"
            output_file = tmp_path / "output.json"
            index_file.write_text(json.dumps({"images": entries, "category": anchor}))

            proc = self._run(
                [str(self._photus_a_bin), str(index_file), "--output", str(output_file)],
                cwd=self._photus_a_root,
                what="Photus A",
            )
            if not output_file.is_file():
                raise EvaluationEngineError(
                    f"Photus A não gerou output.json (exit={proc.returncode}): "
                    f"{(proc.stderr or proc.stdout)[-1000:]}"
                )
            try:
                output = json.loads(output_file.read_text())
            except json.JSONDecodeError as exc:
                raise EvaluationEngineError(f"output.json do Photus A ilegível: {exc}") from exc

        results = _parse_results(output)
        if proc.returncode != 0 or output.get("error"):
            raise EvaluationEngineError(
                f"Photus A terminou com exit={proc.returncode}: {output.get('error') or proc.stderr[-500:]}",
                partial_results=[r for r in results if r.status != PhotoEvaluationStatus.ERROR],
            )
        return results

    def _run(self, cmd: list[str], cwd: Path, what: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=self._timeout_seconds
            )
        except subprocess.TimeoutExpired as exc:
            raise EvaluationEngineError(
                f"{what} excedeu o timeout de {self._timeout_seconds:g}s."
            ) from exc
        except OSError as exc: 
            raise EvaluationEngineError(f"Não foi possível executar o {what}: {exc}") from exc


def _parse_results(output: dict) -> list[PhotoEvaluationResult]:
    results: list[PhotoEvaluationResult] = []
    for item in output.get("results", []):
        filename = item.get("filename")
        if not filename:
            continue
        results.append(
            build_result(
                filename,
                item.get("status"),
                item.get("final_score"),
                item.get("metrics"),
                item.get("face_metrics"),
                item.get("details"),
            )
        )
    return results
