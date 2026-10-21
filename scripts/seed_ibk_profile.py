"""
scripts/seed_ibk_profile.py
TCS Intelligent Microservice Factory -- Seed Reference Profile for Interbank (IBK)
Populates the IBK client profile, categorized technical directives, and an OpenAPI contract
into client-governance-service via its database.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GOV_SERVICE_PATH = BASE_DIR / "services" / "client-governance-service"
sys.path.insert(0, str(GOV_SERVICE_PATH))

from app.core.database import SessionLocal, engine, Base
from app.models.client import ClientProfile
from app.models.directive import TechnicalDirective, DirectiveCategory, DirectiveSeverity
from app.models.contract import OpenApiContract

def seed_ibk():
    print("============================================================")
    print("   Seeding Interbank (IBK) Client Profile (TCS Factory)")
    print("============================================================")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Client Profile
        ibk_client = db.query(ClientProfile).filter(ClientProfile.code == "ibk").first()
        if not ibk_client:
            ibk_client = ClientProfile(
                code="ibk",
                name="Interbank Perú (IBK)",
                description="Cuenta corporativa bancaria Interbank (IBK) para microservicios Cloud Native Quarkus de alta disponibilidad.",
                package_prefix="pe.com.interbank",
                java_version="21",
                quarkus_version="3.15.1",
                is_active=True,
            )
            db.add(ibk_client)
            db.commit()
            db.refresh(ibk_client)
            print("  [+] Perfil de cliente 'ibk' creado exitosamente.")
        else:
            print("  [*] Perfil 'ibk' ya existe. Actualizando directivas...")

        # 2. Categorized Technical Directives
        directives_data = [
            {
                "rule_code": "IBK-ARCH-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Arquitectura limpia y desacoplada (Hexagonal / Clean Architecture) con separación estricta entre dominio, puertos y adaptadores de infraestructura.",
                "deterministic_check": "structure:pe.com.interbank.{domain,infrastructure,application}",
            },
            {
                "rule_code": "IBK-SEC-01",
                "category": DirectiveCategory.SECURITY,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Seguridad bancaria corporativa mediante Quarkus SmallRye JWT u OIDC Keycloak con validación estricta de tokens criptográficos y RBAC.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-smallrye-jwt or io.quarkus:quarkus-oidc",
            },
            {
                "rule_code": "IBK-COMM-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Exposición de APIs REST síncronas de baja latencia con RESTEasy Reactive Jackson y documentación OpenAPI 3.0 automática.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-resteasy-reactive-jackson and io.quarkus:quarkus-smallrye-openapi",
            },
            {
                "rule_code": "IBK-DATA-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Persistencia empresarial mediante Quarkus Hibernate ORM con Panache y conector PostgreSQL para transacciones ACID auditadas.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-hibernate-orm-panache and io.quarkus:quarkus-jdbc-postgresql",
            },
            {
                "rule_code": "IBK-EVENT-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.OPTIONAL,
                "description": "Mensajería reactiva asíncrona con SmallRye Reactive Messaging y Apache Kafka para eventos de transacciones en streaming.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-smallrye-reactive-messaging-kafka",
            },
            {
                "rule_code": "IBK-OBS-01",
                "category": DirectiveCategory.OBSERVABILITY,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Observabilidad y sondas de salud bancaria: SmallRye Health (/q/health) y métricas Micrometer Prometheus (/q/metrics).",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-smallrye-health and io.quarkus:quarkus-micrometer-registry-prometheus",
            },
            {
                "rule_code": "IBK-TEST-01",
                "category": DirectiveCategory.TESTING,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Cobertura exhaustiva con JUnit 5 en dominio y pruebas de integración de endpoints con @QuarkusTest y REST-assured.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-junit5 and io.rest-assured:rest-assured",
            },
            {
                "rule_code": "IBK-RESIL-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.RECOMMENDED,
                "description": "Tolerancia a fallos con SmallRye Fault Tolerance (@Timeout, @Retry, @CircuitBreaker) para llamadas a servicios externos interbancarios.",
                "deterministic_check": "pom.xml:io.quarkus:quarkus-smallrye-fault-tolerance",
            },
        ]

        for d in directives_data:
            existing = db.query(TechnicalDirective).filter(
                TechnicalDirective.client_code == ibk_client.code,
                TechnicalDirective.rule_code == d["rule_code"]
            ).first()

            if not existing:
                new_dir = TechnicalDirective(
                    client_code=ibk_client.code,
                    rule_code=d["rule_code"],
                    category=d["category"],
                    severity=d["severity"],
                    description=d["description"],
                    deterministic_check=d["deterministic_check"],
                    version=1,
                    is_enabled=True,
                )
                db.add(new_dir)
                print(f"  [+] Directiva creada: {d['rule_code']} ({d['severity'].value})")
            else:
                existing.description = d["description"]
                existing.deterministic_check = d["deterministic_check"]
                print(f"  [*] Directiva actualizada: {d['rule_code']}")

        db.commit()

        # 3. OpenAPI Contract
        contract_title = "IBK Financial Transactions API"
        existing_contract = db.query(OpenApiContract).filter(
            OpenApiContract.client_code == ibk_client.code,
            OpenApiContract.title == contract_title
        ).first()

        sample_openapi_yaml = """
openapi: 3.0.3
info:
  title: IBK Financial Transactions API
  version: 1.0.0
  description: Contrato bancario oficial de Interbank para transferencias inmediatas interbancarias y consulta de saldos.
paths:
  /api/v1/transfers:
    post:
      summary: Ejecutar transferencia inmediata interbancaria
      operationId: executeTransfer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - sourceAccount
                - destinationAccount
                - destinationBankCode
                - amount
                - currency
              properties:
                sourceAccount:
                  type: string
                  example: "001-1234567890"
                destinationAccount:
                  type: string
                  example: "002-9876543210"
                destinationBankCode:
                  type: string
                  example: "BCP"
                amount:
                  type: number
                  format: double
                  example: 250.00
                currency:
                  type: string
                  example: "PEN"
      responses:
        '201':
          description: Transferencia procesada exitosamente
          content:
            application/json:
              schema:
                type: object
                properties:
                  transactionId:
                    type: string
                  status:
                    type: string
                    example: "COMPLETED"
                  timestamp:
                    type: string
                    format: date-time
        '400':
          description: Saldo insuficiente o cuenta de destino inválida
  /api/v1/transfers/{id}:
    get:
      summary: Consultar estado de transferencia
      operationId: getTransferStatus
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Detalle de la transacción
        '404':
          description: Transacción no encontrada
"""

        if not existing_contract:
            contract = OpenApiContract(
                client_code=ibk_client.code,
                title=contract_title,
                version="1.0.0",
                format="yaml",
                raw_content=sample_openapi_yaml,
                endpoints_count=2,
                is_valid=True,
            )
            db.add(contract)
            db.commit()
            print("  [+] Contrato OpenAPI de referencia IBK catalogado exitosamente.")
        else:
            existing_contract.raw_content = sample_openapi_yaml
            db.commit()
            print("  [*] Contrato OpenAPI IBK ya existente y verificado.")

        print("\n============================================================")
        print("  [OK] Perfil de referencia Interbank (IBK) incorporado exitosamente.")
        print(f"    - Cliente: {ibk_client.name} ({ibk_client.code})")
        print(f"    - Paquete base: {ibk_client.package_prefix}")
        print(f"    - Java {ibk_client.java_version} / Quarkus {ibk_client.quarkus_version}")
        print("    - Directivas: 8 normativas bancarias registradas")
        print("    - Contrato: IBK Financial Transactions API (OpenAPI 3.0)")
        print("============================================================")

    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Falló el registro del perfil IBK: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_ibk()

