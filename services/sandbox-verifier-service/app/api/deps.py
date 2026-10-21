from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    """Verify bearer token with zero-latency local cryptographic validation."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    local_data = _decode_jwt_local(token)
    if local_data and local_data.get("valid"):
        return local_data

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_client_access(client_code: str, user: Dict[str, Any]) -> None:
    """Check whether the user is authorized to verify/download projects for this client."""
    if user.get("role") == "ADMIN":
        return

    assigned = user.get("assigned_clients", [])
    if "*" in assigned or client_code.lower() in [c.lower() for c in assigned]:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: You are not assigned to client '{client_code}'."
    )

