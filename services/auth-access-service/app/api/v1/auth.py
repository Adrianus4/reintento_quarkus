from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_client_ip, get_current_user, get_db
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.models.assignment import UserClientAssignment
from app.models.audit import AuditLoginLog
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    SetupAdminRequest,
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.user import UserResponse

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


@router.get("/system-status")
def get_system_status(db: Session = Depends(get_db)) -> Any:
    """Return whether initial administrator has been initialized (Zero-State check)."""
    user_count = db.query(User).count()
    return {
        "is_initialized": user_count > 0,
        "user_count": user_count
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user; only the first user may bootstrap administrator access.
    """
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    target_role = UserRole.ADMIN if db.query(User).count() == 0 else UserRole.DEVELOPER

    if not user:
        user = User(
            email=email_clean,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name.strip(),
            role=target_role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        raise HTTPException(status_code=409, detail="Email already registered. Sign in with the existing password.")

    ip = get_client_ip(request)
    audit = AuditLoginLog(
        user_id=user.id,
        email_attempted=email_clean,
        success=True,
        ip_address=ip
    )
    db.add(audit)
    db.commit()

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        role=role_str
    )

    user_resp = _build_user_response(user, db)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )


@router.post("/setup-admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def setup_initial_admin(
    payload: SetupAdminRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Bootstrap the initial administrator once, with immediate token issuance.
    """
    if db.query(User).count() > 0:
        raise HTTPException(status_code=409, detail="Initial administrator setup has already been completed.")
    email_clean = payload.email.lower().strip()
    admin_user = db.query(User).filter(User.email == email_clean).first()

    if not admin_user:
        admin_user = User(
            email=email_clean,
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name.strip(),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    ip = get_client_ip(request)
    audit = AuditLoginLog(
        user_id=admin_user.id,
        email_attempted=email_clean,
        success=True,
        ip_address=ip
    )
    db.add(audit)
    db.commit()

    role_str = "ADMIN"
    access_token = create_access_token(
        subject=admin_user.id,
        email=admin_user.email,
        role=role_str
    )

    user_resp = _build_user_response(admin_user, db)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate user, record audit log, and return signed JWT.
    """
    ip = get_client_ip(request)
    email_clean = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        audit = AuditLoginLog(
            user_id=user.id if user else None,
            email_attempted=email_clean,
            success=False,
            ip_address=ip
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        audit = AuditLoginLog(
            user_id=user.id,
            email_attempted=email_clean,
            success=False,
            ip_address=ip
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Contact an administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Success audit
    audit = AuditLoginLog(
        user_id=user.id,
        email_attempted=email_clean,
        success=True,
        ip_address=ip
    )
    db.add(audit)
    db.commit()

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        subject=user.id,
        email=user.email,
        role=role_str
    )

    user_resp = _build_user_response(user, db)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Return currently authenticated user profile with assigned clients."""
    return _build_user_response(current_user, db)


@router.get("/me/clients")
def get_current_user_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Return client account codes authorized for the authenticated user.
    Admins receive wildcard ['*'], developers receive their strictly assigned clients.
    """
    if current_user.role == UserRole.ADMIN:
        return {
            "user_id": current_user.id,
            "role": "ADMIN",
            "is_admin": True,
            "client_codes": ["*"]
        }

    assignments = db.query(UserClientAssignment).filter(
        UserClientAssignment.user_id == current_user.id
    ).all()
    client_codes = [a.client_code for a in assignments]
    return {
        "user_id": current_user.id,
        "role": "DEVELOPER",
        "is_admin": False,
        "client_codes": client_codes
    }


@router.post("/verify", response_model=TokenVerifyResponse)
def verify_token(
    payload: TokenVerifyRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Inter-service endpoint: verify token authenticity, active status, and client permissions.
    """
    decoded = decode_access_token(payload.token)
    if not decoded:
        return TokenVerifyResponse(
            valid=False,
            reason="INVALID_OR_EXPIRED_TOKEN"
        )

    user_id = decoded.get("sub")
    if not user_id:
        return TokenVerifyResponse(
            valid=False,
            reason="INVALID_TOKEN_SUBJECT"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return TokenVerifyResponse(
            valid=False,
            reason="USER_NOT_FOUND"
        )

    if not user.is_active:
        return TokenVerifyResponse(
            valid=False,
            reason="USER_INACTIVE"
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    if user.role == UserRole.ADMIN:
        assigned = ["*"]
    else:
        assignments = db.query(UserClientAssignment).filter(
            UserClientAssignment.user_id == user.id
        ).all()
        assigned = [a.client_code for a in assignments]

    return TokenVerifyResponse(
        valid=True,
        user_id=user.id,
        email=user.email,
        role=role_str,
        assigned_clients=assigned,
        reason=None
    )
