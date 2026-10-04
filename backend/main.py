from fastapi import FastAPI
from backend.core.config import settings
from backend.database.database import engine, Base
from backend.models.models import Tenant, User
from backend.routes import auth

# Cria as tabelas na base de dados SQLite automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nexa Gestão SaaS", version="1.0.0")

# Inclui as rotas de autenticação
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {
        "message": "Bem-vindo à API Nexa Gestão",
        "status": "online",
        "database": "tabelas criadas com sucesso"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}