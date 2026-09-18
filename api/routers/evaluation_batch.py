from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from api.deps import get_submit_evaluation_batch_use_case, get_usuario_id_atual
from api.schemas.evaluation_batch import BatchPublic
from domain.application.dtos.evaluation_batch_dto import PhotoUploadRequest, SubmitBatchRequest
from domain.application.use_cases.submit_evaluation_batch import SubmitEvaluationBatch

router = APIRouter(tags=["batches"])


@router.post("/batches", response_model=BatchPublic, status_code=status.HTTP_201_CREATED)
def submit_evaluation_batch(
    input_text: Annotated[str, Form(...)],
    photos: Annotated[list[UploadFile], File(default_factory=list)],
    user_id: Annotated[str, Depends(get_usuario_id_atual)],
    use_case: Annotated[SubmitEvaluationBatch, Depends(get_submit_evaluation_batch_use_case)],
) -> BatchPublic:
    photo_uploads = [
        PhotoUploadRequest(file_name=photo.filename, content=photo.file.read())
        for photo in photos
    ]
    result = use_case.execute(
        SubmitBatchRequest(user_id=user_id, input_text=input_text, photos=photo_uploads)
    )
    return BatchPublic(
        id=result.id,
        user_id=result.user_id,
        input_text=result.input_text,
        status=result.status,
        classified_anchor=result.classified_anchor,
        classification_route=result.classification_route,
        created_at=result.created_at,
    )
