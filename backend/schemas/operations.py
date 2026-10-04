from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0, le=1_000_000)
    quantity: int = Field(ge=0, le=10_000_000)
    min_quantity: int = Field(default=0, ge=0, le=10_000_000)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    price: float | None = Field(default=None, gt=0, le=1_000_000)
    quantity: int | None = Field(default=None, ge=0, le=10_000_000)
    min_quantity: int | None = Field(default=None, ge=0, le=10_000_000)


class StockMovementCreate(BaseModel):
    movement_type: Literal["entrada", "saida"]
    quantity: int = Field(gt=0, le=10_000_000)
    reason: str = Field(default="", max_length=200)


class EmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    role: str = Field(min_length=2, max_length=50)
    contact: str = Field(default="", max_length=120)
    shift: str = Field(default="Integral", max_length=30)
    salary: float = Field(default=0, ge=0, le=10_000_000)
    account_email: EmailStr | None = None
    account_password: str | None = Field(default=None, min_length=12, max_length=72)
    account_role: Literal["manager", "waiter", "kitchen"] = "waiter"

    @field_validator("account_email")
    @classmethod
    def normalize_account_email(cls, value: EmailStr | None) -> str | None:
        return str(value).strip().lower() if value else None

    @model_validator(mode="after")
    def validate_optional_account(self) -> "EmployeeCreate":
        if bool(self.account_email) != bool(self.account_password):
            raise ValueError("E-mail e senha de acesso devem ser informados juntos")
        if self.account_password and len(self.account_password.encode("utf-8")) > 72:
            raise ValueError("A senha de acesso deve ter no máximo 72 bytes")
        return self


class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    role: str | None = Field(default=None, min_length=2, max_length=50)
    contact: str | None = Field(default=None, max_length=120)
    shift: str | None = Field(default=None, max_length=30)
    status: Literal["Ativo", "Inativo"] | None = None
    salary: float | None = Field(default=None, ge=0, le=10_000_000)


class TableCreate(BaseModel):
    table_num: str = Field(min_length=1, max_length=40)
    client_name: str = Field(default="", max_length=100)
    status: Literal["ocupada", "livre"] = "ocupada"
    total: float = Field(default=0, ge=0, le=10_000_000)


class TableUpdate(BaseModel):
    client_name: str | None = Field(default=None, max_length=100)
    status: Literal["ocupada", "livre", "fechada"] | None = None
    total: float | None = Field(default=None, ge=0, le=10_000_000)


class KitchenOrderCreate(BaseModel):
    order_num: str = Field(min_length=1, max_length=30)
    table_num: str = Field(min_length=1, max_length=40)
    items: str = Field(min_length=1, max_length=2000)
    status: Literal["preparando", "pronto"] = "preparando"


class KitchenOrderUpdate(BaseModel):
    status: Literal["preparando", "pronto"]


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=50)
    transaction_type: Literal["receita", "despesa"]
    amount: float = Field(gt=0, le=100_000_000)


class ActivityCreate(BaseModel):
    occurred_at: str | None = Field(default=None, max_length=30)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=240)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    subdomain: str | None = Field(default=None, min_length=2, max_length=63)

    @field_validator("subdomain", mode="before")
    @classmethod
    def normalize_tenant_subdomain(cls, value: str | None) -> str | None:
        return str(value).strip().lower() if value is not None else None

    @field_validator("subdomain")
    @classmethod
    def validate_tenant_subdomain(cls, value: str | None) -> str | None:
        if value is not None and (
            not value[0].isalnum()
            or not value[-1].isalnum()
            or any(not (character.isalnum() or character == "-") for character in value)
        ):
            raise ValueError("Use apenas letras, números e hífen no subdomínio")
        return value


class AdminTenantUpdate(BaseModel):
    plan: Literal["basico", "pro", "enterprise"] | None = None
    subscription_status: Literal["active", "trialing", "past_due", "canceled"] | None = None


class UserAccessUpdate(BaseModel):
    role: Literal["manager", "waiter", "kitchen"] | None = None
    is_active: bool | None = None


class AdminTenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    subdomain: str = Field(min_length=2, max_length=63)
    owner_name: str = Field(min_length=2, max_length=100)
    owner_email: EmailStr
    owner_password: str = Field(min_length=12, max_length=72)
    plan: Literal["basico", "pro", "enterprise"] = "pro"

    @field_validator("owner_email")
    @classmethod
    def normalize_owner_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("subdomain", mode="before")
    @classmethod
    def normalize_admin_subdomain(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("subdomain")
    @classmethod
    def validate_admin_subdomain(cls, value: str) -> str:
        if not value[0].isalnum() or not value[-1].isalnum() or any(not (c.isalnum() or c == "-") for c in value):
            raise ValueError("Use apenas letras, números e hífen no subdomínio")
        return value

    @field_validator("owner_password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes")
        return value