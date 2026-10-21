import json
import os
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, verify_client_access
from app.core.compiler import run_compilation_verification
from app.core.config import settings
from app.core.database import get_db
from app.core.manifest import generate_manifest, write_manifest_file
from app.core.packager import create_zip_archive, materialize_files
from app.models.run import VerificationRun
from app.schemas.verifier import RunCreateRequest, RunResponse

router = APIRouter()


def _format_run_response(run: VerificationRun) -> RunResponse:
    manifest_obj = json.loads(run.manifest_json) if run.manifest_json else None
    return RunResponse(
        id=run.id,
        user_id=run.user_id,
        client_code=run.client_code,
        job_id=run.job_id,
        status=run.status,
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
    """Materialize files in ephemeral sandbox, compile, generate SHA-256 manifest, and create zip."""
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

    # 3. Execute compilation and testing
    is_success, output, duration_ms = run_compilation_verification(workspace_dir)
    status_str = "SUCCESS" if is_success else "COMPILATION_FAILED"

    # 4. Generate SHA-256 manifest and save to workspace
    manifest = generate_manifest(
        run_id=run.id,
        client_code=code_clean,
        status=status_str,
        files=payload.files,
    )
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
    """Retrieve verification run diagnostics, timing, and compilation output."""
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
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Download verified Quarkus microservice as ZIP archive."""
    run = db.query(VerificationRun).filter(VerificationRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification run not found"
        )

    verify_client_access(run.client_code, user)

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

