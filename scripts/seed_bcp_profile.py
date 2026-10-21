"""
scripts/seed_bcp_profile.py
TCS Intelligent Microservice Factory -- Seed Reference Profile for BCP
Populates the client profile, categorized technical directives, and a sample OpenAPI contract
into client-governance-service via its internal database or REST API.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add services/client-governance-service to sys.path so we can use its models directly
BASE_DIR = Path(__file__).resolve().parent.parent
GOV_SERVICE_PATH = BASE_DIR / "services" / "client-governance-service"
sys.path.insert(0, str(GOV_SERVICE_PATH))

from app.core.database import SessionLocal, engine, Base
from app.models.client import ClientProfile
from app.models.directive import TechnicalDirective, DirectiveCategory, DirectiveSeverity
from app.models.contract import OpenApiContract

def seed_bcp():
    print("============================================================")
    print("   Seeding BCP Reference Pilot Profile (TCS Factory)")
    print("============================================================")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Client Profile
        bcp_client = db.query(ClientProfile).filter(ClientProfile.code == "bcp").first()
        if not bcp_client:
            bcp_client = ClientProfile(
                code="bcp",
                name="Banco de Crédito del Perú (BCP)",
                description="Cuenta piloto bancaria de referencia para microservicios Quarkus en TCS.",
                package_prefix="pe.com.bcp",
                java_version="21",
                quarkus_version="3.15.1",
                is_active=True,
            )
            db.add(bcp_client)
            db.commit()
            db.refresh(bcp_client)
            print("  [+] Perfil de cliente 'bcp' creado exitosamente.")
        else:
            print("  [*] Perfil 'bcp' ya existe. Actualizando directivas...")

        # 2. Categorized Technical Directives (Pillars 1 to 7)
        directives_data = [
            # Pillar 1: Lenguaje y Framework
            {
                "rule_code": "BCP-LANG-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Uso estricto de Java 17 o Java 21 LTS con Quarkus Core, ArC CDI y RESTEasy Reactive para endpoints HTTP.",
                "deterministic_check": "pom.xml:java.version in [17, 21] and io.quarkus:quarkus-resteasy-reactive",
            },
            {
                "rule_code": "BCP-LANG-02",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.RECOMMENDED,
                "description": "Adhesión rigurosa a principios SOLID, Clean Code y separación en capas desacopladas (Domain, Application, Infrastructure).",
                "deterministic_check": "package_structure_clean",
            },

            # Pillar 2: APIs e Integración
            {
                "rule_code": "BCP-API-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Exposición de contratos OpenAPI 3.0 mediante SmallRye OpenAPI (quarkus-smallrye-openapi) alineados para publicación en Azure APIM.",
                "deterministic_check": "io.quarkus:quarkus-smallrye-openapi in pom.xml",
            },

            # Pillar 3: Arquitectura Reactiva y Eventos (Opcional / Por Demanda)
            {
                "rule_code": "BCP-EVENT-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.OPTIONAL,
                "description": "Integración reactiva con Mutiny y SmallRye Reactive Messaging para Apache Kafka o Azure Service Bus. Incluir únicamente cuando el requerimiento justifique mensajería asíncrona, Saga o Outbox.",
                "deterministic_check": "io.quarkus:quarkus-smallrye-reactive-messaging-kafka in pom.xml",
            },

            # Pillar 4: Seguridad y Cifrado
            {
                "rule_code": "BCP-SEC-01",
                "category": DirectiveCategory.SECURITY,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Autenticación basada en JWT/OIDC con Quarkus Security (quarkus-smallrye-jwt). Prohibido almacenamiento de credenciales o secretos en código plano (utilizar Azure Key Vault).",
                "deterministic_check": "io.quarkus:quarkus-smallrye-jwt in pom.xml and zero_hardcoded_passwords",
            },

            # Pillar 5: Pruebas y Calidad
            {
                "rule_code": "BCP-TEST-01",
                "category": DirectiveCategory.TESTING,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Pruebas automatizadas obligatorias con JUnit 5, @QuarkusTest, Mockito y REST-assured. Cobertura determinista de endpoints y reglas de negocio.",
                "deterministic_check": "io.quarkus:quarkus-junit5 and io.rest-assured:rest-assured in pom.xml",
            },

            # Pillar 6: Persistencia y Base de Datos
            {
                "rule_code": "BCP-DATA-01",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Persistencia relacional con Hibernate ORM with Panache y driver JDBC para SQL Server / Azure SQL. Modelamiento en 3FN y prevención estricta de consultas N+1.",
                "deterministic_check": "io.quarkus:quarkus-hibernate-orm-panache and io.quarkus:quarkus-jdbc-mssql in pom.xml",
            },
            {
                "rule_code": "BCP-DATA-NOSQL-02",
                "category": DirectiveCategory.ARCHITECTURE,
                "severity": DirectiveSeverity.OPTIONAL,
                "description": "Soporte NoSQL con MongoDB o Azure Cosmos DB habilitado únicamente para catálogos o auditorías no transaccionales que lo demanden.",
                "deterministic_check": "io.quarkus:quarkus-mongodb-panache in pom.xml",
            },

            # Pillar 7: Cloud & CI/CD
            {
                "rule_code": "BCP-CLOUD-01",
                "category": DirectiveCategory.OBSERVABILITY,
                "severity": DirectiveSeverity.MANDATORY,
                "description": "Generación de Dockerfile multinivel para Kubernetes / Azure Container Apps y pipeline .github/workflows/ci.yml con compilación y pruebas 'mvn -B clean test'.",
                "deterministic_check": "ci_workflow_present",
            },
        ]

        # Insert or update directives
        for d in directives_data:
            existing_dir = db.query(TechnicalDirective).filter(
                TechnicalDirective.client_code == "bcp",
                TechnicalDirective.rule_code == d["rule_code"]
            ).first()

            if not existing_dir:
                new_dir = TechnicalDirective(
                    client_code="bcp",
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
                existing_dir.description = d["description"]
                existing_dir.category = d["category"]
                existing_dir.severity = d["severity"]
                existing_dir.deterministic_check = d["deterministic_check"]
                print(f"  [*] Directiva actualizada: {d['rule_code']} ({d['severity'].value})")

        db.commit()

        # 3. OpenAPI Reference Contract (BCP Transferencias)
        sample_openapi_yaml = """openapi: 3.0.3
info:
  title: BCP Transferencias Interbancarias API
  description: Contrato de referencia de transferencias de fondos con idempotencia y validación de saldos para BCP.
  version: 1.0.0
paths:
  /api/v1/transfers:
    post:
      summary: Realizar transferencia interbancaria inmediata
      operationId: createTransfer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - source_account
                - destination_account
                - amount
                - currency
              properties:
                source_account:
                  type: string
                  example: "191-12345678-0-01"
                destination_account:
                  type: string
                  example: "002-87654321-1-99"
                amount:
                  type: number
                  format: double
                  example: 250.00
                currency:
                  type: string
                  example: "PEN"
                idempotency_key:
                  type: string
                  example: "uuid-idem-987654"
      responses:
        '201':
          description: Transferencia procesada exitosamente
          content:
            application/json:
              schema:
                type: object
                properties:
                  operation_id:
                    type: string
                  status:
                    type: string
                    example: "COMPLETED"
                  timestamp:
                    type: string
                    format: date-time
        '400':
          description: Saldo insuficiente o datos inválidos
"""

        contract_title = "BCP Transferencias Interbancarias API"
        existing_contract = db.query(OpenApiContract).filter(
            OpenApiContract.client_code == "bcp",
            OpenApiContract.title == contract_title
        ).first()

        if not existing_contract:
            new_contract = OpenApiContract(
                client_code="bcp",
                title=contract_title,
                version="1.0.0",
                raw_content=sample_openapi_yaml,
                endpoints_count=1,
            )
            db.add(new_contract)
            db.commit()
            print("  [+] Contrato OpenAPI de referencia catalogado exitosamente.")
        else:
            print("  [*] Contrato OpenAPI ya catalogado.")

        print()
        print("============================================================")
        print("  [OK] Perfil de referencia BCP incorporado exitosamente.")
        print("    - Cliente: Banco de Crédito del Perú (BCP)")
        print("    - Directivas: 9 normativas registradas (Obligatorias vs Opcionales)")
        print("    - Contrato: Transferencias API (OpenAPI 3.0)")
        print("============================================================")

    finally:
        db.close()

if __name__ == "__main__":
    seed_bcp()
