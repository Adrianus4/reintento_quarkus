from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
import jwt
from app.core.config import settings
from app.core.database import get_db

security_scheme = HTTPBearer(auto_error=False)


def _decode_jwt_local(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        role = payload.get("role", "DEVELOPER")
        assigned = ["*"] if role == "ADMIN" else payload.get("assigned_clients", [])
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": role,
            "assigned_clients": assigned,
        }
    except Exception:
        return None


def get_verified_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    Verify bearer token with local cryptographic validation (sub-millisecond)
    or remote auth-access-service verification.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 1. Fast cryptographic JWT decoding (Zero network overhead)
    local_data = _decode_jwt_local(token)
    if local_data and local_data.get("valid"):
        return local_data

    # 2. Remote check if configured and local failed
    if hasattr(settings, "REMOTE_AUTH_VERIFY") and getattr(settings, "REMOTE_AUTH_VERIFY"):
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.post(
                    settings.AUTH_SERVICE_VERIFY_URL,
                    json={"token": token}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("valid"):
                        return data
        except httpx.RequestError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(user: Dict[str, Any] = Depends(get_verified_user)) -> Dict[str, Any]:
    """Ensure caller has corporate ADMIN role."""
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this operation"
        )
    return user


def verify_client_access(client_code: str, user: Dict[str, Any]) -> None:
    """Check whether the user is authorized to read/operate on this client account."""
    if user.get("role") == "ADMIN":
        return

    assigned = user.get("assigned_clients", [])
    if "*" in assigned or client_code.lower() in [c.lower() for c in assigned]:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: You are not assigned to client '{client_code}'."
    )
