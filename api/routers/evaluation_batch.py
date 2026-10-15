from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status

from api.deps import (
    get_evaluation_job,
    get_get_evaluation_batch_use_case,
    get_submit_evaluation_batch_use_case,
    get_usuario_id_atual,
)
from api.schemas.evaluation_batch import BatchDetailPublic, BatchPublic
from domain.application.dtos.evaluation_batch_dto import PhotoUploadRequest, SubmitBatchRequest
from domain.application.use_cases.get_evaluation_batch import GetEvaluationBatch
from domain.application.use_cases.submit_evaluation_batch import SubmitEvaluationBatch
from domain.entities.evaluation_batch import BatchStatus
from infra.jobs.evaluation_job import EvaluationJob

router = APIRouter(tags=["batches"])


@router.post("/batches", response_model=BatchPublic, status_code=status.HTTP_201_CREATED)
def submit_evaluation_batch(
    input_text: Annotated[str, Form(...)],
    photos: Annotated[list[UploadFile], File(default_factory=list)],
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_usuario_id_atual)],
    use_case: Annotated[SubmitEvaluationBatch, Depends(get_submit_evaluation_batch_use_case)],
    evaluation_job: Annotated[EvaluationJob, Depends(get_evaluation_job)],
) -> BatchPublic:
    photo_uploads = [
        PhotoUploadRequest(file_name=photo.filename, content=photo.file.read())
        for photo in photos
    ]
    result = use_case.execute(
        SubmitBatchRequest(user_id=user_id, input_text=input_text, photos=photo_uploads)
    )
    # UC05 -> UC06: se a âncora foi classificada (lote não caiu em `erro`), a
    # avaliação técnica roda DEPOIS da resposta, em background; o front
    # acompanha por GET /batches/{id} (em_processamento -> concluido|erro).
    if result.status == BatchStatus.PROCESSING and result.classified_anchor is not None:
        background_tasks.add_task(evaluation_job, result.id)
    return BatchPublic(
        id=result.id,
        user_id=result.user_id,
        input_text=result.input_text,
        status=result.status,
        classified_anchor=result.classified_anchor,
        classification_route=result.classification_route,
        created_at=result.created_at,
    )


@router.get("/batches/{batch_id}", response_model=BatchDetailPublic)
def get_evaluation_batch(
    batch_id: str,
    user_id: Annotated[str, Depends(get_usuario_id_atual)],
    use_case: Annotated[GetEvaluationBatch, Depends(get_get_evaluation_batch_use_case)],
) -> BatchDetailPublic:
    detail = use_case.execute(batch_id, user_id)
    return BatchDetailPublic.model_validate(asdict(detail))
