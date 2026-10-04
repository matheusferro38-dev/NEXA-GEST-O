from dataclasses import dataclass
from datetime import datetime
import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database.database import get_db
from backend.models.models import AuthSession, Tenant, User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUserTenant:
    user_id: int
    tenant_id: int
    email: str
    role: str
    session_id: str


def get_current_user_tenant(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUserTenant:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada. Entre novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise unauthorized

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
        session_id = str(payload["sid"])
        tenant_id = int(payload["tid"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise unauthorized

    now = datetime.utcnow()
    auth_session = (
        db.query(AuthSession)
        .filter(
            AuthSession.id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.tenant_id == tenant_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .first()
    )
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not auth_session or not user or not user.is_active or not tenant or not tenant.is_active:
        raise unauthorized

    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.cookies.get(settings.SESSION_COOKIE_NAME):
        csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME, "")
        csrf_header = request.headers.get("X-CSRF-Token", "")
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requisição não autorizada.")

    return CurrentUserTenant(
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        role=user.role,
        session_id=auth_session.id,
    )


def require_roles(*allowed_roles: str):
    def role_dependency(current: CurrentUserTenant = Depends(get_current_user_tenant)) -> CurrentUserTenant:
        if current.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para esta ação.")
        return current

    return role_dependency