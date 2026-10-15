
from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from api.deps import build_evaluation_pipeline
from domain.application.exceptions.evaluation_batch_exceptions import EvaluationEngineError
from domain.application.interfaces.photo_evaluation_pipeline import PhotoToEvaluate
from domain.entities.evaluated_photo import PhotoEvaluationStatus
from infra.config import Settings
from infra.pipeline.http_engine_pipeline import HttpPhotoEvaluationPipeline
from infra.pipeline.local_cpp_pipeline import LocalCppPipeline

OK_BODY = {
    "batch_id": "b1",
    "anchor": "sublime",
    "thresholds_file": "sublime_thresholds.json",
    "thresholds_source": "specific",
    "results": [
        {"file_name": "a.jpg", "status": "Aprovado", "final_score": 0.9,
         "metrics": {"sharpness": 1.0}, "face_metrics": {"confidence": 0.1}, "details": None},
        {"file_name": "b.jpg", "status": "Revisao_Humana", "final_score": 0.5,
         "metrics": {}, "face_metrics": None, "details": "x"},
        {"file_name": "c.jpg", "status": "error", "final_score": None,
         "metrics": {}, "face_metrics": None, "details": "Falha ao carregar a imagem"},
    ],
}


@pytest.fixture
def photos(tmp_path: Path) -> list[PhotoToEvaluate]:
    out = []
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        f = tmp_path / name
        f.write_bytes(b"jpeg-" + name.encode())
        out.append(PhotoToEvaluate(name, str(f)))
    return out


def _pipeline(handler) -> HttpPhotoEvaluationPipeline:
    return HttpPhotoEvaluationPipeline(
        "http://engine:8000/", timeout_seconds=5, transport=httpx.MockTransport(handler)
    )


def test_envia_multipart_e_mapeia_os_status_do_engine(photos) -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json=OK_BODY)

    outcome = _pipeline(handler).run("b1", "sublime", photos)

    assert seen["url"] == "http://engine:8000/v1/evaluate"
    for fragment in (b'name="batch_id"', b"b1", b'name="anchor"', b"sublime",
                     b'filename="a.jpg"', b"jpeg-a.jpg", b'filename="c.jpg"'):
        assert fragment in seen["body"]
    assert outcome.thresholds_file == "sublime_thresholds.json"
    assert outcome.thresholds_source == "specific"
    assert [r.status for r in outcome.results] == [
        PhotoEvaluationStatus.APPROVED,
        PhotoEvaluationStatus.HUMAN_REVIEW,  # "Revisao_Humana" cru -> enum
        PhotoEvaluationStatus.ERROR,
    ]
    assert outcome.results[0].metrics == {"sharpness": 1.0}
    assert outcome.results[2].final_score is None


def test_http_500_com_resultados_parciais_vira_engine_error(photos) -> None:
    body = {
        "detail": "Photus A terminou com exit=1: boom",
        "partial_results": [OK_BODY["results"][0], OK_BODY["results"][2]],
    }
    pipeline = _pipeline(lambda request: httpx.Response(500, json=body))

    with pytest.raises(EvaluationEngineError, match="HTTP 500.*exit=1") as erro:
        pipeline.run("b1", "sublime", photos)

    # só o que foi de fato avaliado é preservado (o item `error` fica de fora)
    assert [r.file_name for r in erro.value.partial_results] == ["a.jpg"]


def test_resposta_nao_json_do_engine_vira_engine_error(photos) -> None:
    pipeline = _pipeline(lambda request: httpx.Response(502, text="Bad Gateway"))

    with pytest.raises(EvaluationEngineError, match="HTTP 502"):
        pipeline.run("b1", "sublime", photos)


@pytest.mark.parametrize(
    "erro",
    [httpx.ConnectError("conexão recusada"), httpx.ReadTimeout("timeout")],
)
def test_engine_indisponivel_ou_timeout_vira_engine_error(photos, erro) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise erro

    with pytest.raises(EvaluationEngineError, match="indisponível"):
        _pipeline(handler).run("b1", "sublime", photos)


def test_fotos_inexistentes_em_disco_nao_chamam_o_engine() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("não deveria chamar o engine")

    with pytest.raises(EvaluationEngineError, match="existe em disco"):
        _pipeline(handler).run("b1", "sublime", [PhotoToEvaluate("x.jpg", "/nao/existe/x.jpg")])


def test_backend_configurado_escolhe_o_adapter() -> None:
    assert isinstance(build_evaluation_pipeline(Settings(pipeline_backend="http")),
                      HttpPhotoEvaluationPipeline)
    assert isinstance(build_evaluation_pipeline(Settings(pipeline_backend="local")),
                      LocalCppPipeline)
