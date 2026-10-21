from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import require_admin, get_db
from app.core.security import get_password_hash
from app.models.assignment import UserClientAssignment
from app.models.user import User, UserRole
from app.schemas.user import ClientAssignmentUpdate, UserCreate, UserResponse, UserUpdate

router = APIRouter()


def _build_user_response(user: User, db: Session) -> UserResponse:
    assignments = db.query(UserClientAssignment).filter(UserClientAssignment.user_id == user.id).all()
    assigned_clients = [a.client_code for a in assignments]
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active,
        created_at=user.created_at,
        assigned_clients=assigned_clients,
    )


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: Optional[str] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """List all corporate users with pagination and optional role filter. Requires ADMIN role."""
    query = db.query(User)
    if role:
        role_upper = role.upper()
        if role_upper in ["ADMIN", "DEVELOPER"]:
            query = query.filter(User.role == UserRole(role_upper))
    
    users = query.offset(skip).limit(limit).all()
    return [_build_user_response(u, db) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new collaborator with strictly ADMIN or DEVELOPER role. Requires ADMIN role."""
    email_clean = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{email_clean}' already exists."
        )

    try:
        assigned_role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role. Must be 'ADMIN' or 'DEVELOPER'."
        )

    new_user = User(
        email=email_clean,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _build_user_response(new_user, db)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Update user information, role, or active status. Prevents self-deactivation of the sole admin."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Self-deactivation / demotion prevention check
    if current_admin.id == target_user.id:
        active_admins = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()

        if payload.is_active is False and active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the sole active Administrator."
            )
        if payload.role == "DEVELOPER" and active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke administrator role from the sole active Administrator."
            )

    if payload.full_name is not None:
        target_user.full_name = payload.full_name.strip()

    if payload.role is not None:
        try:
            target_user.role = UserRole(payload.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid role. Must be 'ADMIN' or 'DEVELOPER'."
            )

    if payload.is_active is not None:
        target_user.is_active = payload.is_active

    if payload.password is not None:
        target_user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(target_user)
    return _build_user_response(target_user, db)


@router.put("/{user_id}/assigned-clients", response_model=UserResponse)
def assign_clients_to_user(
    user_id: str,
    payload: ClientAssignmentUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Assign authorized client account codes to a user. Overwrites previous assignments."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Clear existing assignments
    db.query(UserClientAssignment).filter(UserClientAssignment.user_id == user_id).delete()

    # Deduplicate and normalize client codes
    clean_codes = set(code.strip().lower() for code in payload.client_codes if code.strip())

    for code in clean_codes:
        assignment = UserClientAssignment(
            user_id=target_user.id,
            client_code=code,
            assigned_by_user_id=current_admin.id
        )
        db.add(assignment)

    db.commit()
    db.refresh(target_user)
    return _build_user_response(target_user, db)

