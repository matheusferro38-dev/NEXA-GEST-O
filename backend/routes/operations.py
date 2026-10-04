from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.security import get_password_hash
from backend.core.tenancy import CurrentUserTenant, get_current_user_tenant, require_roles
from backend.database.database import get_db
from backend.models.models import (
    Activity,
    AuthSession,
    Employee,
    FinancialTransaction,
    InventoryMovement,
    KitchenOrder,
    Product,
    TableOrder,
    Tenant,
    User,
)
from backend.schemas.auth import TenantResponse
from backend.schemas.operations import (
    ActivityCreate,
    EmployeeCreate,
    EmployeeUpdate,
    KitchenOrderCreate,
    KitchenOrderUpdate,
    ProductCreate,
    ProductUpdate,
    StockMovementCreate,
    TableCreate,
    TableUpdate,
    TenantUpdate,
    TransactionCreate,
)

router = APIRouter(tags=["Operations"])


def _product_data(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "quantity": product.quantity,
        "min_quantity": product.min_quantity,
        "created_at": product.created_at,
    }


def _employee_data(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "contact": employee.contact,
        "shift": employee.shift,
        "status": employee.status,
        "salary": employee.salary,
        "has_access": employee.user_id is not None,
    }


def _table_data(table: TableOrder) -> dict:
    return {
        "id": table.id,
        "table_num": table.table_num,
        "client_name": table.client_name,
        "status": table.status,
        "total": table.total,
        "created_at": table.created_at,
        "updated_at": table.updated_at,
    }


def _kitchen_order_data(order: KitchenOrder) -> dict:
    return {
        "id": order.id,
        "order_num": order.order_num,
        "table_num": order.table_num,
        "items": order.items,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _transaction_data(transaction: FinancialTransaction) -> dict:
    return {
        "id": transaction.id,
        "description": transaction.description,
        "category": transaction.category,
        "transaction_type": transaction.transaction_type,
        "amount": transaction.amount,
        "date": transaction.transaction_date,
        "source_order_id": transaction.source_order_id,
    }


def _get_tenant_product(db: Session, product_id: int, tenant_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return product


@router.get("/dashboard/summary")
def dashboard_summary(
    current: CurrentUserTenant = Depends(get_current_user_tenant),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    start_of_day = datetime.combine(now.date(), time.min)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def transaction_total(transaction_type: str, since: datetime) -> float:
        total = (
            db.query(func.coalesce(func.sum(FinancialTransaction.amount), 0))
            .filter(
                FinancialTransaction.tenant_id == current.tenant_id,
                FinancialTransaction.transaction_type == transaction_type,
                FinancialTransaction.transaction_date >= since,
            )
            .scalar()
        )
        return float(total or 0)

    table_counts = dict(
        db.query(TableOrder.status, func.count(TableOrder.id))
        .filter(TableOrder.tenant_id == current.tenant_id)
        .group_by(TableOrder.status)
        .all()
    )
    kitchen_counts = dict(
        db.query(KitchenOrder.status, func.count(KitchenOrder.id))
        .filter(KitchenOrder.tenant_id == current.tenant_id)
        .group_by(KitchenOrder.status)
        .all()
    )
    products_count = db.query(func.count(Product.id)).filter(Product.tenant_id == current.tenant_id).scalar() or 0
    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(Product.tenant_id == current.tenant_id, Product.quantity <= Product.min_quantity)
        .scalar()
        or 0
    )
    active_employees = (
        db.query(func.count(Employee.id))
        .filter(Employee.tenant_id == current.tenant_id, Employee.status == "Ativo")
        .scalar()
        or 0
    )
    orders_today = (
        db.query(func.count(KitchenOrder.id))
        .filter(KitchenOrder.tenant_id == current.tenant_id, KitchenOrder.created_at >= start_of_day)
        .scalar()
        or 0
    )
    revenue_today = transaction_total("receita", start_of_day)
    revenue_month = transaction_total("receita", start_of_month)
    expenses_month = transaction_total("despesa", start_of_month)
    tenant = db.query(Tenant).filter(Tenant.id == current.tenant_id).first()

    return {
        "sales_today": revenue_today,
        "orders_today": int(orders_today),
        "products_count": int(products_count),
        "low_stock_count": int(low_stock_count),
        "tables_total": sum(table_counts.values()),
        "tables_occupied": int(table_counts.get("ocupada", 0)),
        "tables_free": int(table_counts.get("livre", 0)),
        "kitchen_preparing": int(kitchen_counts.get("preparando", 0)),
        "kitchen_ready": int(kitchen_counts.get("pronto", 0)),
        "employees_count": int(active_employees),
        "revenue_month": revenue_month,
        "expenses_month": expenses_month,
        "net_month": revenue_month - expenses_month,
        "subscription_status": tenant.subscription_status if tenant else "unknown",
    }


@router.get("/products/categories")
def list_product_categories(
    current: CurrentUserTenant = Depends(get_current_user_tenant),
    db: Session = Depends(get_db),
):
    categories = (
        db.query(Product.category)
        .filter(Product.tenant_id == current.tenant_id)
        .distinct()
        .order_by(Product.category)
        .all()
    )
    return [category[0] for category in categories]


@router.get("/products")
def list_products(
    current: CurrentUserTenant = Depends(get_current_user_tenant),
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .filter(Product.tenant_id == current.tenant_id)
        .order_by(Product.name)
        .all()
    )
    return [_product_data(product) for product in products]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    product = Product(tenant_id=current.tenant_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_data(product)


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    product = _get_tenant_product(db, product_id, current.tenant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return _product_data(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    product = _get_tenant_product(db, product_id, current.tenant_id)
    movement_count = (
        db.query(func.count(InventoryMovement.id))
        .filter(InventoryMovement.product_id == product_id, InventoryMovement.tenant_id == current.tenant_id)
        .scalar()
        or 0
    )
    if movement_count:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Produto com movimentações não pode ser excluído.")
    db.delete(product)
    db.commit()


@router.post("/products/{product_id}/stock", status_code=status.HTTP_201_CREATED)
def create_stock_movement(
    product_id: int,
    payload: StockMovementCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    product = _get_tenant_product(db, product_id, current.tenant_id)
    if payload.movement_type == "saida" and product.quantity < payload.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Estoque insuficiente para essa saída.")

    delta = payload.quantity if payload.movement_type == "entrada" else -payload.quantity
    product.quantity += delta
    movement = InventoryMovement(
        tenant_id=current.tenant_id,
        product_id=product.id,
        user_id=current.user_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reason=payload.reason.strip(),
    )
    db.add(movement)
    db.commit()
    db.refresh(product)
    return {"product": _product_data(product), "movement_id": movement.id}


@router.get("/inventory/movements")
def list_stock_movements(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    movements = (
        db.query(InventoryMovement)
        .filter(InventoryMovement.tenant_id == current.tenant_id)
        .order_by(InventoryMovement.created_at.desc())
        .limit(500)
        .all()
    )
    return [
        {
            "id": movement.id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "reason": movement.reason,
            "created_at": movement.created_at,
        }
        for movement in movements
    ]


@router.get("/employees")
def list_employees(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    employees = (
        db.query(Employee)
        .filter(Employee.tenant_id == current.tenant_id)
        .order_by(Employee.name)
        .all()
    )
    return [_employee_data(employee) for employee in employees]


@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    user = None
    if payload.account_email:
        if current.role != "owner" and payload.account_role == "manager":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Somente o proprietário pode criar gestores.")
        if db.query(User.id).filter(User.email == payload.account_email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já possui um acesso.")
        user = User(
            email=payload.account_email,
            hashed_password=get_password_hash(payload.account_password or ""),
            tenant_id=current.tenant_id,
            role=payload.account_role,
            is_active=True,
        )
        db.add(user)
        db.flush()

    employee = Employee(
        tenant_id=current.tenant_id,
        user_id=user.id if user else None,
        name=payload.name.strip(),
        role=payload.role.strip(),
        contact=payload.contact.strip(),
        shift=payload.shift,
        status="Ativo",
        salary=payload.salary,
    )
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível criar o acesso ou funcionário.") from error
    db.refresh(employee)
    return _employee_data(employee)


@router.patch("/employees/{employee_id}")
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id, Employee.tenant_id == current.tenant_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado.")
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("status") == "Inativo" and employee.user_id:
        linked_user = db.query(User).filter(User.id == employee.user_id, User.tenant_id == current.tenant_id).first()
        if linked_user:
            linked_user.is_active = False
            db.query(AuthSession).filter(AuthSession.user_id == linked_user.id, AuthSession.revoked_at.is_(None)).update(
                {AuthSession.revoked_at: datetime.utcnow()}, synchronize_session=False
            )
    for field, value in updates.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return _employee_data(employee)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id, Employee.tenant_id == current.tenant_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado.")
    if employee.user_id:
        linked_user = db.query(User).filter(User.id == employee.user_id, User.tenant_id == current.tenant_id).first()
        if linked_user:
            linked_user.is_active = False
            db.query(AuthSession).filter(AuthSession.user_id == linked_user.id, AuthSession.revoked_at.is_(None)).update(
                {AuthSession.revoked_at: datetime.utcnow()}, synchronize_session=False
            )
    db.delete(employee)
    db.commit()


@router.get("/tables")
def list_tables(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter")),
    db: Session = Depends(get_db),
):
    tables = db.query(TableOrder).filter(TableOrder.tenant_id == current.tenant_id).order_by(TableOrder.id.desc()).all()
    return [_table_data(table) for table in tables]


@router.post("/tables", status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter")),
    db: Session = Depends(get_db),
):
    table = TableOrder(tenant_id=current.tenant_id, **payload.model_dump())
    db.add(table)
    db.commit()
    db.refresh(table)
    return _table_data(table)


@router.patch("/tables/{table_id}")
def update_table(
    table_id: int,
    payload: TableUpdate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter")),
    db: Session = Depends(get_db),
):
    table = db.query(TableOrder).filter(TableOrder.id == table_id, TableOrder.tenant_id == current.tenant_id).first()
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa ou comanda não encontrada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(table, field, value)
    table.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(table)
    return _table_data(table)


@router.post("/tables/{table_id}/checkout", status_code=status.HTTP_201_CREATED)
def checkout_table(
    table_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter")),
    db: Session = Depends(get_db),
):
    table = db.query(TableOrder).filter(TableOrder.id == table_id, TableOrder.tenant_id == current.tenant_id).first()
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa ou comanda não encontrada.")
    if table.status != "ocupada":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Somente mesas ocupadas podem ser finalizadas.")
    if db.query(FinancialTransaction.id).filter(FinancialTransaction.source_order_id == table.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta comanda já foi finalizada.")

    transaction = FinancialTransaction(
        tenant_id=current.tenant_id,
        user_id=current.user_id,
        description=f"Venda da mesa {table.table_num}",
        category="Vendas",
        transaction_type="receita",
        amount=table.total,
        source_order_id=table.id,
    )
    table.status = "fechada"
    table.updated_at = datetime.utcnow()
    db.add(transaction)
    db.commit()
    db.refresh(table)
    return {"table": _table_data(table), "transaction": _transaction_data(transaction)}


@router.delete("/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    table = db.query(TableOrder).filter(TableOrder.id == table_id, TableOrder.tenant_id == current.tenant_id).first()
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa ou comanda não encontrada.")
    if db.query(FinancialTransaction.id).filter(FinancialTransaction.source_order_id == table.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Uma comanda finalizada não pode ser excluída.")
    db.delete(table)
    db.commit()


@router.get("/kitchen/orders")
def list_kitchen_orders(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter", "kitchen")),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(KitchenOrder)
        .filter(KitchenOrder.tenant_id == current.tenant_id)
        .order_by(KitchenOrder.created_at.desc())
        .all()
    )
    return [_kitchen_order_data(order) for order in orders]


@router.post("/kitchen/orders", status_code=status.HTTP_201_CREATED)
def create_kitchen_order(
    payload: KitchenOrderCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "waiter", "kitchen")),
    db: Session = Depends(get_db),
):
    order = KitchenOrder(tenant_id=current.tenant_id, **payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return _kitchen_order_data(order)


@router.patch("/kitchen/orders/{order_id}")
def update_kitchen_order(
    order_id: int,
    payload: KitchenOrderUpdate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "kitchen")),
    db: Session = Depends(get_db),
):
    order = db.query(KitchenOrder).filter(KitchenOrder.id == order_id, KitchenOrder.tenant_id == current.tenant_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")
    order.status = payload.status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return _kitchen_order_data(order)


@router.delete("/kitchen/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kitchen_order(
    order_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager", "kitchen")),
    db: Session = Depends(get_db),
):
    order = db.query(KitchenOrder).filter(KitchenOrder.id == order_id, KitchenOrder.tenant_id == current.tenant_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")
    db.delete(order)
    db.commit()


@router.get("/transactions")
def list_transactions(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(FinancialTransaction)
        .filter(FinancialTransaction.tenant_id == current.tenant_id)
        .order_by(FinancialTransaction.transaction_date.desc())
        .limit(1000)
        .all()
    )
    return [_transaction_data(transaction) for transaction in transactions]


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    transaction = FinancialTransaction(
        tenant_id=current.tenant_id,
        user_id=current.user_id,
        **payload.model_dump(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return _transaction_data(transaction)


@router.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: TransactionCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(FinancialTransaction)
        .filter(FinancialTransaction.id == transaction_id, FinancialTransaction.tenant_id == current.tenant_id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lançamento não encontrado.")
    if transaction.source_order_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Uma venda de mesa não pode ser editada por aqui.")
    for field, value in payload.model_dump().items():
        setattr(transaction, field, value)
    db.commit()
    db.refresh(transaction)
    return _transaction_data(transaction)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(FinancialTransaction)
        .filter(FinancialTransaction.id == transaction_id, FinancialTransaction.tenant_id == current.tenant_id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lançamento não encontrado.")
    if transaction.source_order_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Uma venda vinculada à mesa não pode ser excluída.")
    db.delete(transaction)
    db.commit()


@router.get("/activities")
def list_activities(
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(Activity.tenant_id == current.tenant_id)
        .order_by(Activity.occurred_at.desc())
        .limit(200)
        .all()
    )
    return [
        {"id": activity.id, "occurred_at": activity.occurred_at, "category": activity.category, "description": activity.description}
        for activity in activities
    ]


@router.post("/activities", status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    occurred_at = datetime.utcnow()
    if payload.occurred_at:
        try:
            parsed_time = datetime.strptime(payload.occurred_at, "%H:%M").time()
            occurred_at = datetime.combine(occurred_at.date(), parsed_time)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Informe a hora no formato HH:MM.")
    activity = Activity(
        tenant_id=current.tenant_id,
        user_id=current.user_id,
        occurred_at=occurred_at,
        category=payload.category.strip(),
        description=payload.description.strip(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return {"id": activity.id, "occurred_at": activity.occurred_at, "category": activity.category, "description": activity.description}


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: int,
    current: CurrentUserTenant = Depends(require_roles("owner", "manager")),
    db: Session = Depends(get_db),
):
    activity = db.query(Activity).filter(Activity.id == activity_id, Activity.tenant_id == current.tenant_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apontamento não encontrado.")
    db.delete(activity)
    db.commit()


@router.get("/tenants/me")
def get_current_tenant(
    current: CurrentUserTenant = Depends(get_current_user_tenant),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == current.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estabelecimento não encontrado.")
    return TenantResponse.model_validate(tenant)


@router.patch("/tenants/me")
def update_current_tenant(
    payload: TenantUpdate,
    current: CurrentUserTenant = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == current.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estabelecimento não encontrado.")
    updates = payload.model_dump(exclude_unset=True)
    if "subdomain" in updates and db.query(Tenant.id).filter(
        Tenant.subdomain == updates["subdomain"], Tenant.id != current.tenant_id
    ).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este subdomínio já está em uso.")
    if "name" in updates and db.query(Tenant.id).filter(
        Tenant.name == updates["name"], Tenant.id != current.tenant_id
    ).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este nome já está em uso.")
    for field, value in updates.items():
        setattr(tenant, field, value.strip())
    db.commit()
    db.refresh(tenant)
    return TenantResponse.model_validate(tenant)