from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, verify_client_access
from app.core.database import get_db
from app.core.openapi_validator import parse_and_validate_openapi
from app.models.client import ClientProfile
from app.models.contract import OpenApiContract
from app.schemas.contract import ContractResponse, ContractUploadRequest

router = APIRouter()


@router.get("/{client_code}/contracts", response_model=List[ContractResponse])
def list_client_contracts(
    client_code: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all OpenAPI contracts cataloged for a client."""
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found"
        )

    contracts = db.query(OpenApiContract).filter(
        OpenApiContract.client_code == code_clean
    ).order_by(OpenApiContract.created_at.desc()).all()
    return contracts


@router.post("/{client_code}/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def upload_contract(
    client_code: str,
    payload: ContractUploadRequest,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Upload, validate, and catalog an OpenAPI 3.x specification for a client."""
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found"
        )

    is_valid, parsed_title, parsed_version, endpoints_count, error_msg = parse_and_validate_openapi(payload.raw_content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid OpenAPI contract: {error_msg}"
        )

    title_final = payload.title.strip() if payload.title else parsed_title
    version_final = payload.version.strip() if payload.version else parsed_version

    contract = OpenApiContract(
        client_code=code_clean,
        title=title_final,
        version=version_final,
        format=payload.format,
        raw_content=payload.raw_content,
        endpoints_count=endpoints_count,
        is_valid=True,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/{client_code}/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(
    client_code: str,
    contract_id: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve full OpenAPI contract content."""
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    contract = db.query(OpenApiContract).filter(
        OpenApiContract.id == contract_id,
        OpenApiContract.client_code == code_clean
    ).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found for this client"
        )
    return contract

