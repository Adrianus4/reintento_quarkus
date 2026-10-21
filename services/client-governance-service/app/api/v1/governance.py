from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, verify_client_access
from app.core.database import get_db
from app.models.client import ClientProfile
from app.models.contract import OpenApiContract
from app.models.directive import DirectiveSeverity, TechnicalDirective
from app.schemas.contract import ContractResponse
from app.schemas.directive import DirectiveResponse
from app.schemas.governance import GovernanceContextResponse

router = APIRouter()


@router.get("/{client_code}/governance-context", response_model=GovernanceContextResponse)
def get_governance_context(
    client_code: str,
    contract_id: Optional[str] = Query(None, description="Optional target OpenAPI contract ID"),
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Consolidated governance bundle endpoint consumed by ai-orchestrator-service.
    Returns client specifications, categorized active directives, and the chosen contract.
    """
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found"
        )

    directives = db.query(TechnicalDirective).filter(
        TechnicalDirective.client_code == code_clean,
        TechnicalDirective.is_enabled == True
    ).all()

    mandatory = [DirectiveResponse.model_validate(d) for d in directives if d.severity == DirectiveSeverity.MANDATORY]
    recommended = [DirectiveResponse.model_validate(d) for d in directives if d.severity == DirectiveSeverity.RECOMMENDED]
    optional = [DirectiveResponse.model_validate(d) for d in directives if d.severity == DirectiveSeverity.OPTIONAL]

    contract_resp = None
    if contract_id:
        contract = db.query(OpenApiContract).filter(
            OpenApiContract.id == contract_id,
            OpenApiContract.client_code == code_clean
        ).first()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract '{contract_id}' not found for client '{code_clean}'"
            )
        contract_resp = ContractResponse.model_validate(contract)

    return GovernanceContextResponse(
        client=client,
        mandatory_directives=mandatory,
        recommended_directives=recommended,
        optional_directives=optional,
        contract=contract_resp,
        metadata={
            "requested_by_user": user.get("user_id"),
            "caller_role": user.get("role"),
            "total_active_directives": len(directives)
        }
    )

