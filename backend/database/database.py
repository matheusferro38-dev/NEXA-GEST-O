from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.core.config import PROJECT_ROOT, settings


def resolve_database_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    database_path = database_url.removeprefix("sqlite:///")
    if database_path == ":memory:":
        return database_url

    path = Path(database_path)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return f"sqlite:///{path.as_posix()}"


SQLALCHEMY_DATABASE_URL = resolve_database_url(settings.DATABASE_URL)
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite:") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()


def migrate_existing_schema() -> None:
    additive_columns = {
        "tenants": {
            "plan": "VARCHAR(32) NOT NULL DEFAULT 'basico'",
            "subscription_status": "VARCHAR(32) NOT NULL DEFAULT 'active'",
            "created_at": "DATETIME",
        },
        "users": {
            "full_name": "VARCHAR(100) NOT NULL DEFAULT ''",
            "role": "VARCHAR(32) NOT NULL DEFAULT 'owner'",
        },
    }

    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns_to_add in additive_columns.items():
            if not inspector.has_table(table_name):
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_definition in columns_to_add.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()