from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import get_password_hash, verify_password
from backend.core.tenancy import CurrentUserTenant, get_current_user_tenant
from backend.database.database import get_db
from backend.models.models import AuthSession, Tenant, User
from backend.schemas.auth import AuthResponse, TenantResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_session_cookies(response: Response, token: str, csrf_token: str) -> None:
    cookie_options = {
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE.lower(),
        "path": "/",
        "max_age": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        **cookie_options,
    )
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        **cookie_options,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User.id).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está cadastrado.")
    if db.query(Tenant.id).filter(Tenant.subdomain == user_data.tenant_subdomain).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este subdomínio já está em uso.")
    if db.query(Tenant.id).filter(Tenant.name == user_data.tenant_name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um estabelecimento com esse nome.")

    tenant = Tenant(
        name=user_data.tenant_name,
        subdomain=user_data.tenant_subdomain,
        plan="basico",
        subscription_status="trialing",
        is_active=True,
    )
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role="owner",
        is_active=True,
    )
    try:
        db.add(tenant)
        db.flush()
        user.tenant_id = tenant.id
        db.add(user)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ou subdomínio já cadastrado.") from error

    db.refresh(tenant)
    return {
        "message": "Estabelecimento criado. Faça login para continuar.",
        "tenant": TenantResponse.model_validate(tenant),
    }


@router.post("/login", response_model=AuthResponse)
def login_user(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active or user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta conta precisa de assistência do administrador.")

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active or tenant.subscription_status not in {"active", "trialing"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="O acesso deste estabelecimento está suspenso.")

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session_id = str(uuid.uuid4())
    csrf_token = secrets.token_urlsafe(32)
    auth_session = AuthSession(
        id=session_id,
        user_id=user.id,
        tenant_id=tenant.id,
        csrf_token_hash=hashlib.sha256(csrf_token.encode("utf-8")).hexdigest(),
        created_at=now,
        expires_at=expires_at,
    )
    db.add(auth_session)
    db.commit()

    token = jwt.encode(
        {
            "sub": str(user.id),
            "tid": tenant.id,
            "sid": session_id,
            "iat": now,
            "exp": expires_at,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    _set_session_cookies(response, token, csrf_token)
    return {
        "message": "Login efetuado com sucesso.",
        "user": UserResponse.model_validate(user),
        "tenant": TenantResponse.model_validate(tenant),
        "csrf_token": csrf_token,
    }


@router.get("/me")
def get_session(current: CurrentUserTenant = Depends(get_current_user_tenant), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current.user_id, User.tenant_id == current.tenant_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == current.tenant_id).first()
    return {"user": UserResponse.model_validate(user), "tenant": TenantResponse.model_validate(tenant)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current: CurrentUserTenant = Depends(get_current_user_tenant),
    db: Session = Depends(get_db),
):
    auth_session = db.query(AuthSession).filter(AuthSession.id == current.session_id).first()
    if auth_session and auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.utcnow()
        db.commit()
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/", secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE.lower())
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/", secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE.lower())
    response.status_code = status.HTTP_204_NO_CONTENT
    return response