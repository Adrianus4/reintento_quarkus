from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, require_admin, verify_client_access
from app.core.database import get_db
from app.models.client import ClientProfile
from app.models.directive import DirectiveCategory, DirectiveSeverity, TechnicalDirective
from app.schemas.directive import DirectiveCreate, DirectiveResponse, DirectiveUpdate

router = APIRouter()


@router.get("/{client_code}/directives", response_model=List[DirectiveResponse])
def list_client_directives(
    client_code: str,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    only_enabled: bool = True,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """List technical directives for a specific client. Enforces client access isolation."""
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found"
        )

    query = db.query(TechnicalDirective).filter(TechnicalDirective.client_code == code_clean)
    if only_enabled:
        query = query.filter(TechnicalDirective.is_enabled == True)
    if category:
        query = query.filter(TechnicalDirective.category == category.upper())
    if severity:
        query = query.filter(TechnicalDirective.severity == severity.upper())

    return query.order_by(TechnicalDirective.category.asc(), TechnicalDirective.rule_code.asc()).all()


@router.post("/{client_code}/directives", response_model=DirectiveResponse, status_code=status.HTTP_201_CREATED)
def create_client_directive(
    client_code: str,
    payload: DirectiveCreate,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Register a new technical directive for a client. Requires ADMIN role."""
    code_clean = client_code.strip().lower()
    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found"
        )

    rule_code_clean = payload.rule_code.strip().upper()
    existing = db.query(TechnicalDirective).filter(
        TechnicalDirective.client_code == code_clean,
        TechnicalDirective.rule_code == rule_code_clean
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Directive with rule_code '{rule_code_clean}' already exists for client '{code_clean}'."
        )

    directive = TechnicalDirective(
        client_code=code_clean,
        rule_code=rule_code_clean,
        category=DirectiveCategory(payload.category),
        severity=DirectiveSeverity(payload.severity),
        description=payload.description.strip(),
        deterministic_check=payload.deterministic_check.strip() if payload.deterministic_check else None,
        version=1,
        is_enabled=True,
    )
    db.add(directive)
    db.commit()
    db.refresh(directive)
    return directive

