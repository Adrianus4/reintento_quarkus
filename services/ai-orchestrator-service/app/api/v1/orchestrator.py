import io
import json
import zipfile
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, get_optional_user, verify_client_access
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
        "quarkus_version": payload.quarkus_version or "3.15.1",
        "build_tool": payload.build_tool or "maven",
        "design_patterns": payload.design_patterns or [],
        "naming_conventions": payload.naming_conventions or {},
        "event_broker": payload.event_broker or "none",
        "channels": payload.channels or [],
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


@router.get("/jobs/{job_id}/download")
def download_job_zip(
    job_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Download the generated Quarkus microservice files directly as a ZIP archive."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found"
        )

    verify_client_access(job.client_code, user)
    files_dict = json.loads(job.files_json) if job.files_json else {}
    if not files_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=job.error_message or "El trabajo de generación no contiene archivos generados"
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in files_dict.items():
            clean_path = file_path.lstrip("/\\")
            zf.writestr(clean_path, content)

    zip_buffer.seek(0)
    filename = f"{job.client_code}-quarkus-microservice.zip"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


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

    if job.status not in ("AWAITING_REVIEW", "APPROVED") or job.error_message:
        raise HTTPException(status_code=409, detail="Project must pass sandbox verification before approval.")
    job.status = "APPROVED"
    db.commit()
    db.refresh(job)
    return _format_job_response(job)



@router.post("/infer-spec")
def infer_microservice_spec(
    payload: dict,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Analyze natural language requirements and automatically structure all 7 architectural phases."""
    client_code = payload.get("client_code", "bcp").lower()
    requirements = payload.get("requirements", "").strip()
    req_lower = requirements.lower()

    # If real LLM is configured, query the active LLM directly!
    try:
        from app.llm.mock_client import MockLLMClient
        llm = LLMClientFactory.get_client(db)
        if not isinstance(llm, MockLLMClient):
            system_prompt = (
                "You are a Principal Software Architect at TCS specializing in enterprise Quarkus 3.x microservices.\n"
                "Analyze the user's microservice requirement and output ONLY a valid JSON object defining the complete 7-phase architecture specification.\n"
                "JSON format MUST match this exact schema:\n"
                "{\n"
                '  "artifact_id": "string",\n'
                '  "package_prefix": "string",\n'
                '  "http_port": 8080,\n'
                '  "java_version": "21",\n'
                '  "quarkus_version": "3.15.1",\n'
                '  "build_tool": "maven",\n'
                '  "architecture_style": "Hexagonal",\n'
                '  "custom_architecture_notes": "string",\n'
                '  "security_option": "JWT",\n'
                '  "jwt_issuer": "string",\n'
                '  "security_roles": ["ADMIN", "OPERATOR", "AUDITOR"],\n'
                '  "database_option": "SQLSERVER_PANACHE",\n'
                '  "database_name": "string",\n'
                '  "entities": [\n'
                '    {\n'
                '      "name": "EntityName",\n'
                '      "tableName": "table_name",\n'
                '      "fields": [\n'
                '        {"name": "id", "type": "UUID", "required": true, "isId": true},\n'
                '        {"name": "fieldName", "type": "String", "required": true}\n'
                '      ]\n'
                '    }\n'
                '  ],\n'
                '  "custom_endpoints": [\n'
                '    {"method": "POST", "path": "/api/v1/resource", "summary": "string"}\n'
                '  ],\n'
                '  "design_patterns": ["REPOSITORY", "BUILDER", "OUTBOX"],\n'
                '  "event_broker": "kafka",\n'
                '  "event_topic_out": "string",\n'
                '  "event_topic_in": "string"\n'
                "}"
            )
            user_prompt = f"Client: {client_code.upper()}\nRequirement: {requirements}\nProvide at least 2 complete domain entities in the 'entities' array with detailed fields."
            text_resp, _, _ = llm.generate(system_prompt, user_prompt)
            from app.graph.nodes import extract_and_parse_json
            try:
                parsed = extract_and_parse_json(text_resp)
                if isinstance(parsed, dict) and "entities" in parsed and len(parsed["entities"]) > 0:
                    parsed.setdefault("build_tool", "maven")
                    parsed.setdefault("java_version", "21")
                    parsed.setdefault("quarkus_version", "3.15.1")
                    parsed.setdefault("http_port", 8080)
                    parsed.setdefault("architecture_style", "Hexagonal")
                    return parsed
            except Exception:
                pass
    except Exception:
        pass

    # Determine domain from requirement (Fallback when MOCK is active)
    if any(k in req_lower for k in ["poliza", "seguro", "insurance", "siniestro", "asegurad"]):
        domain_name = "polizas"
        entity_name = "Policy"
        table_name = "policies"
        fields = [
            {"name": "id", "type": "UUID", "required": True, "isId": True},
            {"name": "policyNumber", "type": "String", "required": True},
            {"name": "holderDni", "type": "String", "required": True},
            {"name": "insuredVehiclePlate", "type": "String", "required": True},
            {"name": "premiumAmount", "type": "BigDecimal", "required": True},
            {"name": "status", "type": "String", "required": True},
            {"name": "startDate", "type": "LocalDateTime", "required": True},
        ]
        summary_op = "Emisión y evaluación de pólizas de seguro vehicular"
    elif any(k in req_lower for k in ["tarjeta", "credito", "card", "linea", "plastico"]):
        domain_name = "tarjetas"
        entity_name = "CreditCard"
        table_name = "credit_cards"
        fields = [
            {"name": "id", "type": "UUID", "required": True, "isId": True},
            {"name": "cardNumberMasked", "type": "String", "required": True},
            {"name": "holderName", "type": "String", "required": True},
            {"name": "holderDni", "type": "String", "required": True},
            {"name": "creditLimit", "type": "BigDecimal", "required": True},
            {"name": "status", "type": "String", "required": True},
            {"name": "createdAt", "type": "LocalDateTime", "required": True},
        ]
        summary_op = "Apertura y gestión de tarjetas de crédito y asignación de límites"
    elif any(k in req_lower for k in ["prestamo", "loan", "hipotec", "financiamiento", "credito"]):
        domain_name = "prestamos"
        entity_name = "Loan"
        table_name = "loans"
        fields = [
            {"name": "id", "type": "UUID", "required": True, "isId": True},
            {"name": "applicantDni", "type": "String", "required": True},
            {"name": "amount", "type": "BigDecimal", "required": True},
            {"name": "interestRate", "type": "BigDecimal", "required": True},
            {"name": "termMonths", "type": "Integer", "required": True},
            {"name": "status", "type": "String", "required": True},
            {"name": "createdAt", "type": "LocalDateTime", "required": True},
        ]
        summary_op = "Originación y cálculo de cuotas de préstamos"
    elif any(k in req_lower for k in ["transfer", "cuenta", "banc", "giro", "pago", "payment", "saldo"]):
        domain_name = "cuentas"
        entities_list = [
            {
                "name": "Account",
                "tableName": "accounts",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "accountNumber", "type": "String", "required": True},
                    {"name": "currency", "type": "String", "required": True},
                    {"name": "balance", "type": "BigDecimal", "required": True},
                    {"name": "accountType", "type": "String", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "customerId", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            },
            {
                "name": "Transfer",
                "tableName": "transfers",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "sourceAccount", "type": "String", "required": True},
                    {"name": "destinationAccount", "type": "String", "required": True},
                    {"name": "amount", "type": "BigDecimal", "required": True},
                    {"name": "currency", "type": "String", "required": True},
                    {"name": "referenceCode", "type": "String", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "executedAt", "type": "LocalDateTime", "required": True},
                ]
            }
        ]
        endpoints_list = [
            {"method": "POST", "path": "/api/v1/transfers", "summary": "Ejecutar transferencia de fondos entre cuentas"},
            {"method": "GET", "path": "/api/v1/transfers/{id}", "summary": "Consultar comprobante de transferencia"},
            {"method": "GET", "path": "/api/v1/accounts/{id}", "summary": "Consultar saldo y estado de cuenta"},
            {"method": "POST", "path": "/api/v1/accounts", "summary": "Crear nueva cuenta bancaria empresarial"},
        ]
        return {
            "artifact_id": f"{client_code}-cuentas-service",
            "package_prefix": f"pe.com.{client_code}.cuentas",
            "http_port": 8080,
            "java_version": "21",
            "quarkus_version": "3.15.1",
            "build_tool": "maven",
            "architecture_style": "Hexagonal",
            "custom_architecture_notes": f"Arquitectura hexagonal para {client_code.upper()} con puertos in/out, modelos inmutables y trazabilidad transaccional.",
            "security_option": "JWT",
            "jwt_issuer": f"https://auth.via{client_code}.com",
            "security_roles": ["ADMIN", "OPERATOR", "AUDITOR"],
            "database_option": "SQLSERVER_PANACHE" if client_code == "bcp" else "POSTGRESQL_PANACHE",
            "database_name": f"{client_code}_cuentas_db",
            "entities": entities_list,
            "custom_endpoints": endpoints_list,
            "design_patterns": ["REPOSITORY", "BUILDER", "OUTBOX"],
            "event_broker": "kafka",
            "event_topic_out": f"pe.com.{client_code}.transfers.v1",
            "event_topic_in": f"pe.com.{client_code}.notifications.v1",
        }
    elif any(k in req_lower for k in ["cliente", "customer", "usuario", "onboarding"]):
        domain_name = "clientes"
        entity_name = "Customer"
        table_name = "customers"
        fields = [
            {"name": "id", "type": "UUID", "required": True, "isId": True},
            {"name": "dni", "type": "String", "required": True},
            {"name": "fullName", "type": "String", "required": True},
            {"name": "email", "type": "String", "required": True},
            {"name": "phone", "type": "String", "required": True},
            {"name": "status", "type": "String", "required": True},
        ]
        summary_op = "Onboarding y gestión centralizada de clientes"
    else:
        domain_name = "operaciones"
        entity_name = "Operation"
        table_name = "operations"
        fields = [
            {"name": "id", "type": "UUID", "required": True, "isId": True},
            {"name": "operationCode", "type": "String", "required": True},
            {"name": "description", "type": "String", "required": True},
            {"name": "amount", "type": "BigDecimal", "required": True},
            {"name": "status", "type": "String", "required": True},
            {"name": "createdAt", "type": "LocalDateTime", "required": True},
        ]
        summary_op = "Gestión transaccional y registro de operaciones"

    return {
        "artifact_id": f"{client_code}-{domain_name}-service",
        "package_prefix": f"pe.com.{client_code}.{domain_name}",
        "http_port": 8080,
        "java_version": "21",
        "quarkus_version": "3.15.1",
        "build_tool": "maven",
        "architecture_style": "Hexagonal",
        "custom_architecture_notes": f"Arquitectura hexagonal para {client_code.upper()} con puertos in/out, modelos inmutables y trazabilidad transaccional.",
        "security_option": "JWT",
        "jwt_issuer": f"https://auth.via{client_code}.com",
        "security_roles": ["ADMIN", "OPERATOR", "AUDITOR"],
        "database_option": "SQLSERVER_PANACHE" if client_code == "bcp" else "POSTGRESQL_PANACHE",
        "database_name": f"{client_code}_{domain_name}_db",
        "entities": [
            {
                "name": entity_name,
                "tableName": table_name,
                "fields": fields
            }
        ],
        "custom_endpoints": [
            {
                "method": "POST",
                "path": f"/api/v1/{domain_name}",
                "summary": f"Registrar nuevo {entity_name} con validaciones"
            },
            {
                "method": "GET",
                "path": f"/api/v1/{domain_name}/{{id}}",
                "summary": f"Consultar {entity_name} por identificador UUID"
            },
            {
                "method": "GET",
                "path": f"/api/v1/{domain_name}",
                "summary": f"Listar {entity_name}s con filtros y paginación"
            }
        ],
        "design_patterns": ["REPOSITORY", "BUILDER", "OUTBOX"],
        "event_broker": "kafka",
        "event_topic_out": f"pe.com.{client_code}.{domain_name}.events.v1",
        "event_topic_in": f"pe.com.{client_code}.notifications.events.v1",
    }
