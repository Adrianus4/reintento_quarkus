from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import ClientProfile, DirectiveCategory, DirectiveSeverity, OpenApiContract, TechnicalDirective


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Seed default enterprise clients and governance directives
    db = SessionLocal()
    try:
        ibk = db.query(ClientProfile).filter_by(code="ibk").first()
        if not ibk:
            ibk = ClientProfile(
                code="ibk",
                name="Interbank Perú",
                description="Banco Internacional del Perú - Microservicios Core",
                is_active=True
            )
            db.add(ibk)
            db.flush()
            db.add(TechnicalDirective(
                client_id=ibk.id,
                category=DirectiveCategory.ARCHITECTURE,
                rule_code="IBK-ARCH-001",
                title="Arquitectura Hexagonal Estricta",
                description="Separación obligatoria de puertos, adaptadores y modelos de dominio inmutables.",
                severity=DirectiveSeverity.MANDATORY,
                is_mandatory=True
            ))
            db.add(TechnicalDirective(
                client_id=ibk.id,
                category=DirectiveCategory.SECURITY,
                rule_code="IBK-SEC-001",
                title="Autenticación JWT con Claims Bancarios",
                description="Validación obligatoria de tokens Bearer JWT firmados con emisor https://auth.interbank.pe.",
                severity=DirectiveSeverity.MANDATORY,
                is_mandatory=True
            ))
            db.add(TechnicalDirective(
                client_id=ibk.id,
                category=DirectiveCategory.DATABASE,
                rule_code="IBK-DB-001",
                title="Persistencia PostgreSQL con Panache",
                description="Entidades JPA/Panache con tipos transaccionales ACID y UUIDv4.",
                severity=DirectiveSeverity.MANDATORY,
                is_mandatory=True
            ))

        bcp = db.query(ClientProfile).filter_by(code="bcp").first()
        if not bcp:
            bcp = ClientProfile(
                code="bcp",
                name="Banco de Crédito del Perú",
                description="Banco de Crédito del Perú BCP - Banca Digital",
                is_active=True
            )
            db.add(bcp)
            db.flush()
            db.add(TechnicalDirective(
                client_id=bcp.id,
                category=DirectiveCategory.ARCHITECTURE,
                rule_code="BCP-ARCH-001",
                title="Clean Architecture",
                description="Aislamiento de capas Domain, UseCases e Infrastructure.",
                severity=DirectiveSeverity.MANDATORY,
                is_mandatory=True
            ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TCS Intelligent Microservice Factory — Enterprise Client Governance, Directives & OpenAPI Catalog Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "ok",
        "service": "client-governance-service",
        "port": settings.PORT,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

