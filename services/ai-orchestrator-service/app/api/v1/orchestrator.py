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

    # 4. Build configuration dictionary from payload
    config_dict = {
        "architecture_style": payload.architecture_style or "Hexagonal",
        "custom_architecture_notes": payload.custom_architecture_notes,
        "security_option": payload.security_option or "JWT",
        "jwt_issuer": payload.jwt_issuer,
        "security_roles": payload.security_roles or [],
        "communication_protocol": payload.communication_protocol or "REST",
        "custom_endpoints": payload.custom_endpoints or [],
        "database_option": payload.database_option or "POSTGRESQL_PANACHE",
        "database_name": payload.database_name,
        "package_prefix": payload.package_prefix,
        "artifact_id": payload.artifact_id or "generated-microservice",
        "http_port": payload.http_port or 8080,
        "java_version": payload.java_version or "21",
        "extensions": payload.extensions or [],
        "custom_extensions": payload.custom_extensions or [],
        "custom_properties": payload.custom_properties or {},
        "entities": payload.entities or [],
    }

    # 5. Run LangGraph generation pipeline
    result_state = GenerationWorkflow.run_pipeline(
        job_id=job.id,
        user_id=job.user_id,
        client_code=code_clean,
        requirements=job.requirements,
        contract_id=job.contract_id,
        token=token,
        llm=llm,
        config=config_dict,
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


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    limit: int = 50,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """List recent microservice generation jobs accessible to user."""
    query = db.query(GenerationJob)
    if user.get("role") != "ADMIN":
        assigned = [c.lower() for c in user.get("assigned_clients", [])]
        if "*" not in assigned:
            query = query.filter(GenerationJob.client_code.in_(assigned))
    
    jobs = query.order_by(GenerationJob.created_at.desc()).limit(limit).all()
    return [_format_job_response(j) for j in jobs]


@router.get("/consumption")
def get_consumption_telemetry(
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve token consumption analytics by project and model provider."""
    query = db.query(GenerationJob)
    if user.get("role") != "ADMIN":
        assigned = [c.lower() for c in user.get("assigned_clients", [])]
        if "*" not in assigned:
            query = query.filter(GenerationJob.client_code.in_(assigned))

    all_jobs = query.order_by(GenerationJob.created_at.desc()).all()

    total_prompt = 0
    total_completion = 0
    total_cost = 0.0
    by_provider: dict[str, dict] = {}
    by_client: dict[str, dict] = {}
    records = []

    for j in all_jobs:
        p_tok = j.prompt_tokens or 0
        c_tok = j.completion_tokens or 0
        tot = p_tok + c_tok
        cost = j.cost_usd or 0.0

        total_prompt += p_tok
        total_completion += c_tok
        total_cost += cost

        # Extract project name from blueprint or requirements
        project_name = f"{j.client_code}-microservice"
        provider = "mock"
        if j.blueprint_json:
            try:
                bp = json.loads(j.blueprint_json)
                if bp.get("artifact_id"):
                    project_name = bp["artifact_id"]
                if bp.get("active_provider"):
                    provider = bp["active_provider"]
            except Exception:
                pass

        # Provider aggregation
        if provider not in by_provider:
            by_provider[provider] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0, "jobs_count": 0}
        by_provider[provider]["prompt_tokens"] += p_tok
        by_provider[provider]["completion_tokens"] += c_tok
        by_provider[provider]["total_tokens"] += tot
        by_provider[provider]["cost_usd"] = round(by_provider[provider]["cost_usd"] + cost, 6)
        by_provider[provider]["jobs_count"] += 1

        # Client aggregation
        c_code = j.client_code or "unknown"
        if c_code not in by_client:
            by_client[c_code] = {"total_tokens": 0, "cost_usd": 0.0, "jobs_count": 0}
        by_client[c_code]["total_tokens"] += tot
        by_client[c_code]["cost_usd"] = round(by_client[c_code]["cost_usd"] + cost, 6)
        by_client[c_code]["jobs_count"] += 1

        records.append({
            "job_id": j.id,
            "client_code": j.client_code,
            "project_name": project_name,
            "architecture_style": j.architecture_style or "Hexagonal",
            "status": j.status,
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "total_tokens": tot,
            "cost_usd": round(cost, 6),
            "duration_ms": j.duration_ms or 0,
            "provider": provider,
            "created_at": j.created_at.isoformat() if j.created_at else "",
        })

    return {
        "summary": {
            "total_jobs": len(all_jobs),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "total_cost_usd": round(total_cost, 6),
        },
        "by_provider": by_provider,
        "by_client": by_client,
        "records": records,
    }


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

