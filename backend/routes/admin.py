from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import get_password_hash
from backend.core.tenancy import CurrentUserTenant, require_roles
from backend.database.database import get_db
from backend.models.models import AuthSession, Tenant, User
from backend.schemas.auth import TenantResponse
from backend.schemas.operations import AdminTenantCreate, AdminTenantUpdate

router = APIRouter(prefix="/admin", tags=["SaaS Administration"])
PLAN_PRICES = {"basico": 99, "pro": 199, "enterprise": 399}


def _tenant_data(db: Session, tenant: Tenant) -> dict:
    owner = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.role == "owner")
        .order_by(User.id)
        .first()
    )
    return {
        **TenantResponse.model_validate(tenant).model_dump(),
        "owner_name": owner.full_name if owner else "",
        "owner_email": owner.email if owner else "",
        "owner_count": db.query(User.id).filter(User.tenant_id == tenant.id).count(),
        "monthly_price": PLAN_PRICES.get(tenant.plan, 0),
        "status": tenant.subscription_status,
    }


def _require_platform_admin(current: CurrentUserTenant) -> None:
    if current.role != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito à administração da plataforma.")


@router.get("/overview")
def get_saas_overview(
    current: CurrentUserTenant = Depends(require_roles("platform_admin")),
    db: Session = Depends(get_db),
):
    tenants = db.query(Tenant).all()
    active = [tenant for tenant in tenants if tenant.is_active and tenant.subscription_status in {"active", "trialing"}]
    pending = [tenant for tenant in tenants if tenant.subscription_status == "past_due"]
    mrr = sum(PLAN_PRICES.get(tenant.plan, 0) for tenant in active if tenant.subscription_status == "active")
    return {
        "total_tenants": len(tenants),
        "active_tenants": len(active),
        "pending_tenants": len(pending),
        "mrr": mrr,
    }


@router.get("/tenants")
def list_tenants(
    current: CurrentUserTenant = Depends(require_roles("platform_admin")),
    db: Session = Depends(get_db),
):
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc(), Tenant.id.desc()).all()
    return [_tenant_data(db, tenant) for tenant in tenants]


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: AdminTenantCreate,
    current: CurrentUserTenant = Depends(require_roles("platform_admin")),
    db: Session = Depends(get_db),
):
    if db.query(Tenant.id).filter(Tenant.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um estabelecimento com esse nome.")
    if db.query(Tenant.id).filter(Tenant.subdomain == payload.subdomain).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este subdomínio já está em uso.")
    if db.query(User.id).filter(User.email == payload.owner_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já possui uma conta.")

    tenant = Tenant(
        name=payload.name.strip(),
        subdomain=payload.subdomain,
        plan=payload.plan,
        subscription_status="active",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    try:
        db.add(tenant)
        db.flush()
        owner = User(
            email=payload.owner_email,
            full_name=payload.owner_name.strip(),
            hashed_password=get_password_hash(payload.owner_password),
            tenant_id=tenant.id,
            role="owner",
            is_active=True,
        )
        db.add(owner)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(tenant)
    return _tenant_data(db, tenant)


@router.patch("/tenants/{tenant_id}")
def update_tenant_subscription(
    tenant_id: int,
    payload: AdminTenantUpdate,
    current: CurrentUserTenant = Depends(require_roles("platform_admin")),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estabelecimento não encontrado.")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(tenant, field, value)
    if "subscription_status" in updates:
        tenant.is_active = updates["subscription_status"] != "canceled"
    db.commit()
    db.refresh(tenant)
    return _tenant_data(db, tenant)


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_tenant(
    tenant_id: int,
    current: CurrentUserTenant = Depends(require_roles("platform_admin")),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estabelecimento não encontrado.")
    tenant.is_active = False
    tenant.subscription_status = "canceled"
    users = db.query(User).filter(User.tenant_id == tenant.id).all()
    for user in users:
        user.is_active = False
        db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).update(
            {AuthSession.revoked_at: datetime.utcnow()}, synchronize_session=False
        )
    db.commit()