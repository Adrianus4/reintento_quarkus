from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, require_admin, verify_client_access
from app.core.database import get_db
from app.models.client import ClientProfile
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter()


@router.get("", response_model=List[ClientResponse])
def list_clients(
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """List client profiles. Developers only see accounts they are explicitly assigned to."""
    query = db.query(ClientProfile).filter(ClientProfile.is_active == True)
    
    if user.get("role") != "ADMIN":
        assigned = user.get("assigned_clients", [])
        if "*" not in assigned:
            query = query.filter(ClientProfile.code.in_([c.lower() for c in assigned]))

    clients = query.order_by(ClientProfile.name.asc()).all()
    return clients


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new enterprise client profile. Requires ADMIN role."""
    code_clean = payload.code.strip().lower()
    existing = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client profile with code '{code_clean}' already exists."
        )

    new_client = ClientProfile(
        code=code_clean,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        package_prefix=payload.package_prefix.strip(),
        java_version=payload.java_version,
        quarkus_version=payload.quarkus_version,
        is_active=True,
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


@router.get("/{client_code}", response_model=ClientResponse)
def get_client(
    client_code: str,
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve specific client profile. Enforces client assignment isolation."""
    code_clean = client_code.strip().lower()
    verify_client_access(code_clean, user)

    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found."
        )
    return client


@router.patch("/{client_code}", response_model=ClientResponse)
def update_client(
    client_code: str,
    payload: ClientUpdate,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Update client profile configurations. Requires ADMIN role."""
    code_clean = client_code.strip().lower()
    client = db.query(ClientProfile).filter(ClientProfile.code == code_clean).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{code_clean}' not found."
        )

    if payload.name is not None:
        client.name = payload.name.strip()
    if payload.description is not None:
        client.description = payload.description.strip()
    if payload.package_prefix is not None:
        client.package_prefix = payload.package_prefix.strip()
    if payload.java_version is not None:
        client.java_version = payload.java_version
    if payload.quarkus_version is not None:
        client.quarkus_version = payload.quarkus_version
    if payload.is_active is not None:
        client.is_active = payload.is_active

    db.commit()
    db.refresh(client)
    return client

