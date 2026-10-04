from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    full_name: str = Field(min_length=2, max_length=100)
    tenant_name: str = Field(min_length=2, max_length=100)
    tenant_subdomain: str = Field(min_length=2, max_length=63)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("tenant_name")
    @classmethod
    def clean_tenant_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Informe o nome do estabelecimento")
        return cleaned

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Informe seu nome")
        return cleaned

    @field_validator("tenant_subdomain", mode="before")
    @classmethod
    def normalize_subdomain(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("tenant_subdomain")
    @classmethod
    def validate_subdomain(cls, value: str) -> str:
        if not value[0].isalnum() or not value[-1].isalnum():
            raise ValueError("O subdomínio deve começar e terminar com letra ou número")
        if any(not (character.isalnum() or character == "-") for character in value):
            raise ValueError("Use apenas letras, números e hífen no subdomínio")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A senha deve ter no máximo 72 bytes")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    tenant_id: int
    role: str


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subdomain: str
    plan: str
    subscription_status: str


class AuthResponse(BaseModel):
    message: str
    user: UserResponse
    tenant: TenantResponse
    csrf_token: str


class LoginRequest(UserLogin):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"