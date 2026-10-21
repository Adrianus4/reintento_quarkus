import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, verify_client_access
from app.core.database import get_db
from app.graph.workflow import GenerationWorkflow
from app.llm.factory import LLMClientFactory
from app.models.job import GenerationJob
from app.schemas.job import FileEditRequest, JobCreateRequest, JobResponse

router = APIRouter()


def _format_job_response(job: GenerationJob) -> JobResponse:
    blueprint_obj = json.loads(job.blueprint_json) if job.blueprint_json else None
    files_obj = json.loads(job.files_json) if job.files_json else {}

    return JobResponse(
        id=job.id,
        user_id=job.user_id,
        client_code=job.client_code,
        contract_id=job.contract_id,
        requirements=job.requirements,
        architecture_style=job.architecture_style,
        status=job.status,
        blueprint=blueprint_obj,
        files=files_obj,
        prompt_tokens=job.prompt_tokens,
        completion_tokens=job.completion_tokens,
        cost_usd=job.cost_usd,
        duration_ms=job.duration_ms,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def start_generation_job(
    payload: JobCreateRequest,
    authorization: str = Header(None),
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Execute LangGraph multi-agent microservice generation pipeline."""
    code_clean = payload.client_code.strip().lower()
    verify_client_access(code_clean, user)

    # 1. Create initial job record
    req_text = payload.requirements or payload.raw_requirement or ""
    job = GenerationJob(
        user_id=user.get("user_id", "anonymous"),
        client_code=code_clean,
        contract_id=payload.contract_id,
        requirements=req_text.strip(),
        architecture_style=payload.architecture_style,
        status="IN_PROGRESS",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 2. Extract Bearer token for inter-service calls
    token = authorization.split(" ")[1] if authorization and " " in authorization else ""

    # 3. Get active LLM client
    llm = LLMClientFactory.get_client(db)

    # 4. Run LangGraph generation pipeline
    result_state = GenerationWorkflow.run_pipeline(
        job_id=job.id,
        user_id=job.user_id,
        client_code=code_clean,
        requirements=job.requirements,
        contract_id=job.contract_id,
        token=token,
        llm=llm,
    )

    # 5. Persist final results
    job.status = result_state.get("status", "COMPLETED")
    job.architecture_style = result_state.get("blueprint", {}).get("architecture_style")
    job.blueprint_json = json.dumps(result_state.get("blueprint", {}))
    job.files_json = json.dumps(result_state.get("files", {}))
    job.prompt_tokens = result_state.get("prompt_tokens", 0)
    job.completion_tokens = result_state.get("completion_tokens", 0)
    job.cost_usd = result_state.get("cost_usd", 0.0)
    job.duration_ms = result_state.get("duration_ms", 0)
    job.error_message = result_state.get("error")

    db.commit()
    db.refresh(job)
    return _format_job_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve full generation job details, generated files, and telemetry."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )

    verify_client_access(job.client_code, user)
    return _format_job_response(job)


@router.patch("/jobs/{job_id}/files", response_model=JobResponse)
def edit_job_files(
    job_id: str,
    payload: FileEditRequest,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Human-in-the-loop: Edit or inject files in the generated solution before verification."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )

    verify_client_access(job.client_code, user)

    files_obj = json.loads(job.files_json) if job.files_json else {}
    files_obj.update(payload.files)

    job.files_json = json.dumps(files_obj)
    db.commit()
    db.refresh(job)
    return _format_job_response(job)


@router.post("/jobs/{job_id}/approve", response_model=JobResponse)
def approve_job(
    job_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Human-in-the-loop: Approve the reviewed microservice for sandbox packaging."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )

    verify_client_access(job.client_code, user)

    job.status = "APPROVED"
    db.commit()
    db.refresh(job)
    return _format_job_response(job)

