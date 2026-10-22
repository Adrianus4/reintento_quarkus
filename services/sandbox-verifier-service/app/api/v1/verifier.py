import json
import os
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, verify_client_access
from app.core.compiler import run_compilation_verification
from app.core.config import settings
from app.core.database import get_db
from app.core.manifest import generate_manifest, write_manifest_file
from app.core.packager import create_zip_archive, materialize_files
from app.models.run import VerificationRun
from app.schemas.verifier import RunCreateRequest, RunResponse, StructuredFailure

router = APIRouter()


def _format_run_response(run: VerificationRun) -> RunResponse:
    manifest_obj = json.loads(run.manifest_json) if run.manifest_json else None
    
    verdict = "PASSED"
    veto_applied = False
    failures_list = []
    phase_results_map = {}

    if manifest_obj:
        verdict = manifest_obj.get("verdict", "PASSED" if run.status == "SUCCESS" else "FAILED")
        veto_applied = manifest_obj.get("veto_applied", run.status in ["REJECTED_BY_VETO", "COMPILATION_FAILED", "FAILED"])
        phase_results_map = manifest_obj.get("phase_results", {})
        raw_failures = manifest_obj.get("failures", [])
        for f in raw_failures:
            failures_list.append(StructuredFailure(**f))

    return RunResponse(
        id=run.id,
        user_id=run.user_id,
        client_code=run.client_code,
        job_id=run.job_id,
        status=run.status,
        verdict=verdict,
        veto_applied=veto_applied,
        phase_results=phase_results_map,
        failures=failures_list,
        compilation_output=run.compilation_output,
        duration_ms=run.duration_ms,
        manifest=manifest_obj,
        download_url=f"/api/v1/verifier/runs/{run.id}/download",
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post("/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_and_verify_run(
    payload: RunCreateRequest,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Materialize files in ephemeral sandbox, compile with VETO POWER,
    generate cryptographic manifest, and block delivery if defects are found.
    """
    code_clean = payload.client_code.strip().lower()
    verify_client_access(code_clean, user)

    # 1. Initialize run record
    run = VerificationRun(
        user_id=user.get("user_id", "anonymous"),
        client_code=code_clean,
        job_id=payload.job_id,
        status="INITIALIZED",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    workspace_dir = Path(settings.SANDBOX_BASE_PATH) / run.id
    zip_path = Path(settings.SANDBOX_BASE_PATH) / f"{run.id}.zip"

    # 2. Materialize files with path traversal protection
    try:
        materialize_files(workspace_dir, payload.files)
    except ValueError as exc:
        run.status = "ERROR"
        run.compilation_output = str(exc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    # 3. Execute 5-phase compilation, test suites, and smoke test with VETO POWER
    is_success, output, duration_ms, details = run_compilation_verification(workspace_dir)
    status_str = "SUCCESS" if is_success else "COMPILATION_FAILED"

    # 4. Generate SHA-256 manifest enriched with verdict and structured failures
    manifest = generate_manifest(
        run_id=run.id,
        client_code=code_clean,
        status=status_str,
        files=payload.files,
    )
    manifest["verdict"] = details.get("verdict", "PASSED" if is_success else "FAILED")
    manifest["veto_applied"] = details.get("veto_applied", not is_success)
    manifest["phase_results"] = details.get("phase_results", {})
    manifest["failures"] = details.get("failures", [])

    write_manifest_file(workspace_dir, manifest)

    # 5. Compress entire project including manifest
    create_zip_archive(workspace_dir, zip_path)

    # 6. Update database record
    run.status = status_str
    run.compilation_output = output
    run.duration_ms = duration_ms
    run.manifest_json = json.dumps(manifest)
    run.zip_path = str(zip_path)

    db.commit()
    db.refresh(run)
    return _format_run_response(run)


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve verification run diagnostics, timing, structured failures, and compilation output."""
    run = db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification run not found"
        )

    verify_client_access(run.client_code, user)
    return _format_run_response(run)


@router.get("/runs/{run_id}/manifest")
def get_run_manifest(
    run_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve cryptographic SHA-256 verification manifest."""
    run = db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification run not found"
        )

    verify_client_access(run.client_code, user)
    if not run.manifest_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manifest has not been generated for this run"
        )
    return json.loads(run.manifest_json)


@router.get("/runs/{run_id}/download")
def download_run_zip(
    run_id: str,
    bypass_veto: bool = Query(False, description="Emergency override for debugging only"),
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Download verified Quarkus microservice as ZIP archive.
    STRICT VETO: If run status is REJECTED_BY_VETO or FAILED, download is BLOCKED.
    Never deliver broken projects.
    """
    run = db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification run not found"
        )

    verify_client_access(run.client_code, user)

    # STRICT VETO CHECK
    if run.status in ["REJECTED_BY_VETO", "COMPILATION_FAILED", "FAILED"] and not bypass_veto:
        manifest_obj = json.loads(run.manifest_json) if run.manifest_json else {}
        failures_count = len(manifest_obj.get("failures", []))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"ARTEFACTO VETADO POR EL SANDBOX: El microservicio contiene {failures_count} defecto(s) "
                f"en la verificación de compilación o pruebas de aceptación. Principio de Tolerancia Cero: "
                f"nunca se entrega un microservicio roto. Estado: {run.status}."
            )
        )

    if not run.zip_path or not os.path.exists(run.zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZIP package not found or verification incomplete"
        )

    filename = f"{run.client_code}-microservice.zip"
    return FileResponse(
        path=run.zip_path,
        media_type="application/zip",
        filename=filename,
    )
