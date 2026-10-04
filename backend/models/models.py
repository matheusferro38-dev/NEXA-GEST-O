from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    subdomain = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    plan = Column(String(32), default="basico", nullable=False)
    subscription_status = Column(String(32), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False, default="")
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(32), default="owner", nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tenant = relationship("Tenant", back_populates="users")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    csrf_token_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default="Geral")
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movement_type = Column(String(16), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(200), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    contact = Column(String(120), nullable=False, default="")
    shift = Column(String(30), nullable=False, default="Integral")
    status = Column(String(30), nullable=False, default="Ativo")
    salary = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TableOrder(Base):
    __tablename__ = "table_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    table_num = Column(String(40), nullable=False)
    client_name = Column(String(100), nullable=False, default="")
    status = Column(String(24), nullable=False, default="livre")
    total = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KitchenOrder(Base):
    __tablename__ = "kitchen_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    order_num = Column(String(30), nullable=False)
    table_num = Column(String(40), nullable=False)
    items = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="preparando")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)
    transaction_type = Column(String(16), nullable=False)
    amount = Column(Float, nullable=False)
    source_order_id = Column(Integer, ForeignKey("table_orders.id"), unique=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(String(240), nullable=False)