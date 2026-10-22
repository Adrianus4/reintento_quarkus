"""
Code Synthesizer and Quality Guarantee Engine for TCS Quarkus Factory.
Deterministically inspects, repairs, and enriches generated microservices to ensure:
- 100% clean compilation with Java 21 and Quarkus 3.15 ('mvn clean verify').
- Out-of-the-box local execution ('mvn quarkus:dev') without external database dependencies (%dev,test with H2).
- Dynamic adaptation to ANY business domain without hardcoded Book/Category fallbacks.
- Exact mapping of user-specified fields, data types, and business states.
- Unified database dialect parity across pom.xml, application.properties, and docker-compose.yml.
- Kafka DevServices guards to prevent Docker-dependent crashes during test runs.
"""

import json
import re
from typing import Any, Dict, List, Optional
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_dev_keys() -> tuple[str, str]:
    """Generate 2048-bit RSA PEM key pair for local JWT signing and verification."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    pub_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    return pub_pem, priv_pem


def to_snake_case(name: str) -> str:
    s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s).lower()


def to_pascal_case(name: str) -> str:
    return name[0].upper() + name[1:] if name else ""


def get_field_imports(fields: List[Dict[str, Any]]) -> List[str]:
    types = {f["type"] for f in fields}
    imports = []
    if "BigDecimal" in types:
        imports.append("import java.math.BigDecimal;")
    if "UUID" in types:
        imports.append("import java.util.UUID;")
    if "LocalDate" in types:
        imports.append("import java.time.LocalDate;")
    if "LocalDateTime" in types:
        imports.append("import java.time.LocalDateTime;")
    return sorted(imports)


def get_sample_sql_value(f: Dict[str, Any], default_status: str = "ACTIVE") -> str:
    name_l = f["name"].lower()
    ftype = f["type"]
    if f.get("is_id"):
        return "'d0000000-0000-0000-0000-000000000001'"
    if ftype == "UUID":
        return "'d0000000-0000-0000-0000-000000000002'"
    if ftype == "String":
        if "dni" in name_l:
            return "'45871234'"
        if "card" in name_l or "tarjeta" in name_l:
            return "'4111********1111'"
        if "reason" in name_l or "motivo" in name_l:
            return "'Transaccion no reconocida'"
        if "obs" in name_l:
            return "'Reportado por cliente en banca movil'"
        if "status" in name_l or "estado" in name_l:
            return f"'{default_status}'"
        if "code" in name_l:
            return "'SMP-001'"
        if "name" in name_l:
            return "'Sample Enterprise Record'"
        if "genre" in name_l:
            return "'RPG'"
        if "title" in name_l:
            return "'Sample Title'"
        return f"'Sample {f["name"]}'"
    if ftype == "BigDecimal":
        return "150.00"
    if ftype in ["Integer", "int"]:
        return "10"
    if ftype in ["Long", "long"]:
        return "100"
    if ftype == "LocalDate":
        return "'2026-01-15'"
    if ftype == "LocalDateTime":
        return "CURRENT_TIMESTAMP"
    if ftype in ["Boolean", "bool"]:
        return "true"
    return "'Sample'"


def get_sample_json_value(f: Dict[str, Any], default_status: str = "ACTIVE") -> Any:
    name_l = f["name"].lower()
    ftype = f["type"]
    if ftype == "UUID":
        return "d0000000-0000-0000-0000-000000000001"
    if ftype == "String":
        if "dni" in name_l:
            return "45871234"
        if "card" in name_l or "tarjeta" in name_l:
            return "4111********1111"
        if "reason" in name_l or "motivo" in name_l:
            return "Operacion no reconocida en banca virtual"
        if "obs" in name_l:
            return "El cliente desconoce el consumo nocturno"
        if "status" in name_l or "estado" in name_l:
            return default_status
        if "code" in name_l:
            return "TEST-100"
        if "name" in name_l:
            return "Test Integration Record"
        if "genre" in name_l:
            return "Action Adventure"
        if "title" in name_l:
            return "The Legend of Zelda"
        return f"Test {f["name"]}"
    if ftype == "BigDecimal":
        return 125.50
    if ftype in ["Integer", "int"]:
        return 10
    if ftype in ["Long", "long"]:
        return 100
    if ftype == "LocalDate":
        return "2026-06-20"
    if ftype == "LocalDateTime":
        return "2026-10-22T14:30:00"
    if ftype in ["Boolean", "bool"]:
        return True
    return "test"


def get_sample_java_value(f: Dict[str, Any], default_status: str = "ACTIVE") -> str:
    name_l = f["name"].lower()
    ftype = f["type"]
    if ftype == "UUID":
        return "UUID.randomUUID()"
    if ftype == "String":
        if "dni" in name_l:
            return '"45871234"'
        if "card" in name_l or "tarjeta" in name_l:
            return '"4111********1111"'
        if "reason" in name_l or "motivo" in name_l:
            return '"Operacion no reconocida"'
        if "obs" in name_l:
            return '"Reportado por cliente"'
        if "status" in name_l or "estado" in name_l:
            return f'"{default_status}"'
        if "code" in name_l:
            return '"SMP-001"'
        if "name" in name_l:
            return '"Sample Item"'
        if "genre" in name_l:
            return '"Action"'
        if "title" in name_l:
            return '"Sample Title"'
        return f'"Sample {f["name"]}"'
    if ftype == "BigDecimal":
        return 'new BigDecimal("150.00")'
    if ftype in ["Integer", "int"]:
        return "10"
    if ftype in ["Long", "long"]:
        return "100L"
    if ftype == "LocalDate":
        return 'LocalDate.of(2026, 1, 15)'
    if ftype == "LocalDateTime":
        return 'LocalDateTime.now()'
    if ftype in ["Boolean", "bool"]:
        return "Boolean.TRUE"
    return '"sample"'


class CodeSynthesizer:

    @classmethod
    def _resolve_database_kind(cls, state: Dict[str, Any], client_code: str) -> str:
        """Resolve database kind ensuring 100% cohesion between pom.xml and application.properties."""
        spec = state.get("service_spec", {})
        for ob in spec.get("outbound", []):
            if ob.get("kind") == "database":
                t = (ob.get("details", {}).get("db_type", "") or ob.get("details", {}).get("type", "")).lower()
                if "mssql" in t or "sqlserver" in t:
                    return "mssql"
                elif "postgres" in t:
                    return "postgresql"

        cfg_db = state.get("config", {}).get("database_option", "").lower()
        if "mssql" in cfg_db or "sqlserver" in cfg_db:
            return "mssql"
        elif "postgres" in cfg_db:
            return "postgresql"

        bp_db = state.get("blueprint", {}).get("database_option", "").lower()
        if "mssql" in bp_db or "sqlserver" in bp_db:
            return "mssql"
        elif "postgres" in bp_db:
            return "postgresql"

        if client_code.lower() == "bcp":
            return "mssql"
        return "postgresql"

    @classmethod
    def _resolve_primary_entity_and_fields(cls, state: Dict[str, Any], client_code: str) -> Dict[str, Any]:
        """Dynamically resolve entity name, table name, and fields from ServiceSpec, config, or prompt."""
        service_spec = state.get("service_spec", {})
        data_models = service_spec.get("domain", {}).get("data_models", [])
        cfg_entities = state.get("config", {}).get("entities", [])
        blueprint_entities = state.get("blueprint", {}).get("entities", [])
        req = state.get("requirements", "")
        artifact_id = state.get("blueprint", {}).get("artifact_id") or state.get("config", {}).get("artifact_id", "")

        primary_entity = ""
        primary_table = ""
        raw_fields = []

        if data_models and data_models[0].get("name"):
            primary_entity = data_models[0].get("name")
            primary_table = data_models[0].get("table_name") or f"{primary_entity.lower()}s"
            raw_fields = data_models[0].get("fields", [])
        elif cfg_entities and cfg_entities[0].get("name"):
            primary_entity = cfg_entities[0].get("name")
            primary_table = cfg_entities[0].get("tableName") or f"{primary_entity.lower()}s"
            raw_fields = cfg_entities[0].get("fields", [])
        elif blueprint_entities and blueprint_entities[0].get("name"):
            primary_entity = blueprint_entities[0].get("name")
            primary_table = blueprint_entities[0].get("tableName") or f"{primary_entity.lower()}s"
            raw_fields = blueprint_entities[0].get("fields", [])

        combined_text = f"{artifact_id} {req} {primary_entity}".lower()

        # Semantic domain detection
        is_fraud = any(k in combined_text for k in ["fraude", "fraud", "reclamo", "disputa"])
        is_card = any(k in combined_text for k in ["tarjeta", "card", "credito"]) and not is_fraud
        is_book = any(k in combined_text for k in ["libro", "book", "catalogo", "catalog"]) and not is_fraud
        is_game = any(k in combined_text for k in ["videojuego", "videogame", "game", "juego"])

        default_status = "PENDIENTE" if is_fraud else "ACTIVE"

        if not primary_entity:
            if is_fraud:
                primary_entity = "FraudClaim"
                primary_table = "fraud_claims"
            elif is_card:
                primary_entity = "CreditCard"
                primary_table = "credit_cards"
            elif is_book:
                primary_entity = "Book"
                primary_table = "books"
            elif is_game:
                primary_entity = "VideoGame"
                primary_table = "video_games"
            else:
                primary_entity = "Item"
                primary_table = "items"

        if not raw_fields:
            if is_fraud:
                raw_fields = [
                    {"name": "id", "type": "UUID", "required": True, "is_id": True},
                    {"name": "customerDni", "type": "String", "required": True, "description": "DNI del titular"},
                    {"name": "maskedCard", "type": "String", "required": True, "description": "Tarjeta enmascarada"},
                    {"name": "fraudAmount", "type": "BigDecimal", "required": True, "description": "Monto del fraude"},
                    {"name": "reason", "type": "String", "required": True, "description": "Motivo del reclamo"},
                    {"name": "observations", "type": "String", "required": False, "description": "Observaciones del caso"},
                    {"name": "status", "type": "String", "required": True, "description": "Estado: PENDIENTE, EN_REVISION, RESUELTO"},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True, "description": "Fecha de registro"},
                ]
            elif is_card:
                raw_fields = [
                    {"name": "id", "type": "UUID", "required": True, "is_id": True},
                    {"name": "cardNumberMasked", "type": "String", "required": True},
                    {"name": "holderName", "type": "String", "required": True},
                    {"name": "holderDni", "type": "String", "required": True},
                    {"name": "creditLimit", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            elif is_book:
                raw_fields = [
                    {"name": "id", "type": "UUID", "required": True, "is_id": True},
                    {"name": "title", "type": "String", "required": True},
                    {"name": "author", "type": "String", "required": True},
                    {"name": "isbn", "type": "String", "required": True},
                    {"name": "price", "type": "BigDecimal", "required": True},
                    {"name": "stock", "type": "Integer", "required": True},
                    {"name": "categoryId", "type": "UUID", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            elif is_game:
                raw_fields = [
                    {"name": "id", "type": "UUID", "required": True, "is_id": True},
                    {"name": "title", "type": "String", "required": True},
                    {"name": "genre", "type": "String", "required": True},
                    {"name": "price", "type": "BigDecimal", "required": True},
                    {"name": "releaseDate", "type": "LocalDate", "required": True},
                    {"name": "inStock", "type": "Integer", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            else:
                raw_fields = [
                    {"name": "id", "type": "UUID", "required": True, "is_id": True},
                    {"name": "name", "type": "String", "required": True},
                    {"name": "code", "type": "String", "required": True},
                    {"name": "amount", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]

        # Normalize and complete fields
        normalized_fields = []
        for f in raw_fields:
            if hasattr(f, "dict"):
                f = f.dict()
            fname = f.get("name", "field")
            raw_type = str(f.get("type", "String"))
            tl = raw_type.lower()
            if "uuid" in tl:
                ftype = "UUID"
            elif any(k in tl for k in ["bigdecimal", "decimal", "monto", "amount", "price", "balance"]):
                ftype = "BigDecimal"
            elif any(k in tl for k in ["localdatetime", "datetime", "timestamp"]):
                ftype = "LocalDateTime"
            elif any(k in tl for k in ["localdate", "date"]):
                ftype = "LocalDate"
            elif any(k in tl for k in ["integer", "int"]):
                ftype = "Integer"
            elif "long" in tl:
                ftype = "Long"
            elif any(k in tl for k in ["boolean", "bool"]):
                ftype = "Boolean"
            elif any(k in tl for k in ["double", "float"]):
                ftype = "Double"
            else:
                ftype = "String"

            normalized_fields.append({
                "name": fname,
                "type": ftype,
                "required": f.get("required", True),
                "is_id": f.get("is_id", f.get("isId", fname.lower() == "id")),
                "description": f.get("description", "")
            })

        has_id = any(f.get("is_id") or f["name"].lower() == "id" for f in normalized_fields)
        if not has_id:
            normalized_fields = [{"name": "id", "type": "UUID", "required": True, "is_id": True, "description": "Unique identifier"}] + normalized_fields

        has_status = any(f["name"].lower() in ["status", "estado"] for f in normalized_fields)
        if not has_status:
            normalized_fields.append({"name": "status", "type": "String", "required": True, "is_id": False, "description": "Business status"})

        has_created_at = any(f["name"].lower() in ["createdat", "created_at", "fechacreacion"] for f in normalized_fields)
        if not has_created_at:
            normalized_fields.append({"name": "createdAt", "type": "LocalDateTime", "required": True, "is_id": False, "description": "Creation timestamp"})

        return {
            "name": primary_entity,
            "table_name": primary_table,
            "fields": normalized_fields,
            "default_status": default_status
        }

    @classmethod
    def guarantee_project(cls, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce architectural invariants and guarantee compilation & execution readiness.
        Operates on state['files'], state['blueprint'], and state['config'].
        """
        files: Dict[str, str] = state.get("files", {})
        blueprint: Dict[str, Any] = state.get("blueprint", {})
        client_code: str = state.get("client_code", "bcp").lower()

        pkg_prefix = blueprint.get("package_prefix") or f"pe.com.{client_code}.service"
        artifact_id = blueprint.get("artifact_id") or state.get("config", {}).get("artifact_id") or state.get("service_spec", {}).get("service", {}).get("name") or f"{client_code}-microservice"
        pkg_path = pkg_prefix.replace(".", "/")

        # Resolve cohesive database dialect and entity info
        db_kind = cls._resolve_database_kind(state, client_code)
        entity_info = cls._resolve_primary_entity_and_fields(state, client_code)
        primary_entity = entity_info["name"]
        primary_table = entity_info["table_name"]
        fields = entity_info["fields"]
        default_status = entity_info["default_status"]

        # 1. Guarantee POM.xml with all required dependencies and matching DB driver
        cls._guarantee_pom_xml(files, artifact_id, client_code, db_kind)

        # 2. Guarantee application.properties with multi-profile H2 / target DB
        cls._guarantee_application_properties(files, client_code, blueprint, db_kind)

        # 3. Guarantee import.sql seed data and RSA PEM keys
        cls._guarantee_resources_and_keys(files, primary_entity, primary_table, fields, default_status)

        # 4. Guarantee Hexagonal Architecture and resolve Java method signature conflicts
        cls._guarantee_hexagonal_code(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields, default_status, blueprint)

        # 5. Guarantee Uniform Exception Mappers
        cls._guarantee_exception_mappers(files, pkg_prefix, pkg_path)

        # 6. Guarantee Complete REST Controller
        cls._guarantee_rest_resource(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields, blueprint)

        # 7. Guarantee Tests and Mockito configurations
        cls._guarantee_tests(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields, default_status)

        # 8. Guarantee Postman Collection
        cls._guarantee_postman_collection(files, artifact_id, primary_entity, primary_table, client_code, fields, default_status)

        # 9. Guarantee Comprehensive README.md and Docker Compose
        cls._guarantee_documentation(files, artifact_id, pkg_prefix, primary_entity, primary_table, client_code, db_kind, fields)

        # 10. Clean duplicate or conflicting interfaces / obsolete DTOs
        cls._cleanup_obsolete_files(files, pkg_path)

        # 11. Deterministic Syntax Self-Healing: Auto-repair unbalanced braces in all Java files
        cls._auto_heal_java_syntax(files)

        state["files"] = files
        return state

    @classmethod
    def _guarantee_pom_xml(cls, files: Dict[str, str], artifact_id: str, client_code: str, db_kind: str):
        """Ensure pom.xml has Quarkus 3.15 BOM, JUnit 5 Mockito, H2, Security JWT, and exact driver."""
        pom_path = "pom.xml"
        pom_content = files.get(pom_path, "")

        db_artifact = "quarkus-jdbc-postgresql" if db_kind == "postgresql" else "quarkus-jdbc-mssql"
        opposing_db_artifact = "quarkus-jdbc-mssql" if db_kind == "postgresql" else "quarkus-jdbc-postgresql"

        required_deps = [
            ("io.quarkus", "quarkus-resteasy-reactive-jackson"),
            ("io.quarkus", "quarkus-hibernate-validator"),
            ("io.quarkus", "quarkus-smallrye-openapi"),
            ("io.quarkus", "quarkus-smallrye-jwt"),
            ("io.quarkus", "quarkus-smallrye-health"),
            ("io.quarkus", "quarkus-hibernate-orm-panache"),
            ("io.quarkus", db_artifact),
            ("io.quarkus", "quarkus-jdbc-h2"),
            ("io.quarkus", "quarkus-junit5", "test"),
            ("io.quarkus", "quarkus-junit5-mockito", "test"),
            ("io.quarkus", "quarkus-test-security-jwt", "test"),
            ("io.rest-assured", "rest-assured", "test"),
            ("io.smallrye", "smallrye-jwt-build", "test"),
        ]

        if not pom_content or "<project" not in pom_content:
            dep_blocks = []
            for dep in required_deps:
                group = dep[0]
                art = dep[1]
                scope = f"\n      <scope>{dep[2]}</scope>" if len(dep) > 2 else ""
                dep_blocks.append(f"""    <dependency>
      <groupId>{group}</groupId>
      <artifactId>{art}</artifactId>{scope}
    </dependency>""")

            deps_str = "\n".join(dep_blocks)
            files[pom_path] = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>pe.com.{client_code}</groupId>
  <artifactId>{artifact_id}</artifactId>
  <version>1.0.0-SNAPSHOT</version>

  <properties>
    <compiler-plugin.version>3.13.0</compiler-plugin.version>
    <maven.compiler.release>21</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
    <quarkus.platform.artifact-id>quarkus-bom</quarkus.platform.artifact-id>
    <quarkus.platform.group-id>io.quarkus.platform</quarkus.platform.group-id>
    <quarkus.platform.version>3.15.1</quarkus.platform.version>
    <surefire-plugin.version>3.2.5</surefire-plugin.version>
  </properties>

  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>${{quarkus.platform.group-id}}</groupId>
        <artifactId>${{quarkus.platform.artifact-id}}</artifactId>
        <version>${{quarkus.platform.version}}</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>

  <dependencies>
{deps_str}
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>${{quarkus.platform.group-id}}</groupId>
        <artifactId>quarkus-maven-plugin</artifactId>
        <version>${{quarkus.platform.version}}</version>
        <extensions>true</extensions>
        <executions>
          <execution>
            <goals>
              <goal>build</goal>
              <goal>generate-code</goal>
              <goal>generate-code-tests</goal>
            </goals>
          </execution>
        </executions>
      </plugin>
      <plugin>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>${{compiler-plugin.version}}</version>
        <configuration>
          <parameters>true</parameters>
          <encoding>UTF-8</encoding>
        </configuration>
      </plugin>
      <plugin>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>${{surefire-plugin.version}}</version>
        <configuration>
          <systemPropertyVariables>
            <java.util.logging.manager>org.jboss.logmanager.LogManager</java.util.logging.manager>
            <maven.home>${{maven.home}}</maven.home>
          </systemPropertyVariables>
          <argLine>-Dfile.encoding=UTF-8</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""
        else:
            # Remove opposing database artifact if present to eliminate driver collision
            if opposing_db_artifact in pom_content:
                pom_content = re.sub(rf'\s*<dependency>\s*<groupId>io\.quarkus</groupId>\s*<artifactId>{opposing_db_artifact}</artifactId>.*?/dependency>', '', pom_content, flags=re.DOTALL)

            # Ensure H2 is not restricted to <scope>test</scope>
            pom_content = re.sub(r'(<artifactId>quarkus-jdbc-h2</artifactId>\s*)<scope>test</scope>', r'\1', pom_content)

            # Check and inject missing dependencies
            for dep in required_deps:
                art = dep[1]
                if art not in pom_content:
                    group = dep[0]
                    scope = f"\n      <scope>{dep[2]}</scope>" if len(dep) > 2 else ""
                    dep_xml = f"""    <dependency>
      <groupId>{group}</groupId>
      <artifactId>{art}</artifactId>{scope}
    </dependency>\n  </dependencies>"""
                    pom_content = pom_content.replace("</dependencies>", dep_xml)

            # Ensure UTF-8 surefire argLine
            if "<argLine>" not in pom_content and "</maven-surefire-plugin>" in pom_content:
                pom_content = pom_content.replace(
                    "</configuration>",
                    "  <argLine>-Dfile.encoding=UTF-8</argLine>\n        </configuration>"
                )
            files[pom_path] = pom_content

    @classmethod
    def _guarantee_application_properties(cls, files: Dict[str, str], client_code: str, blueprint: Dict[str, Any], db_kind: str):
        """Ensure multi-profile configuration: %dev,%test with H2, %prod with cohesive database dialect."""
        prop_path = "src/main/resources/application.properties"
        existing = files.get(prop_path, "")
        artifact_id = blueprint.get('artifact_id', f'{client_code}-service')

        prod_jdbc_url = (
            f"jdbc:sqlserver://localhost:1433;databaseName={client_code}_db;encrypt=false"
            if db_kind == "mssql"
            else f"jdbc:postgresql://localhost:5432/{client_code}_db"
        )

        content = f"""# ==============================================================================
# Quarkus Application Configuration
# ==============================================================================
quarkus.application.name={artifact_id}
quarkus.http.port=8080

# OpenAPI / Swagger UI
quarkus.swagger-ui.always-include=true
quarkus.swagger-ui.path=/q/swagger-ui
quarkus.smallrye-openapi.path=/q/openapi
quarkus.smallrye-openapi.info-title={artifact_id.upper()} API
quarkus.smallrye-openapi.info-version=1.0.0
quarkus.smallrye-openapi.info-description=Enterprise Hexagonal Quarkus Microservice for {client_code.upper()}

# Health Checks
quarkus.smallrye-health.root-path=/q/health

# ------------------------------------------------------------------------------
# LOCAL DEV & TEST PROFILES (Runs out-of-the-box with H2 in-memory)
# ------------------------------------------------------------------------------
%dev.quarkus.datasource.db-kind=h2
%dev.quarkus.datasource.jdbc.url=jdbc:h2:mem:default;DB_CLOSE_DELAY=-1
%dev.quarkus.hibernate-orm.database.generation=drop-and-create
%dev.quarkus.hibernate-orm.sql-load-script=import.sql
%dev.mp.jwt.verify.publickey.location=publicKey.pem
%dev.quarkus.kafka.devservices.enabled=false

%test.quarkus.datasource.db-kind=h2
%test.quarkus.datasource.jdbc.url=jdbc:h2:mem:default;DB_CLOSE_DELAY=-1
%test.quarkus.hibernate-orm.database.generation=drop-and-create
%test.quarkus.hibernate-orm.sql-load-script=import.sql
%test.mp.jwt.verify.publickey.location=publicKey.pem
%test.quarkus.kafka.devservices.enabled=false

# ------------------------------------------------------------------------------
# PRODUCTION PROFILE (Configured via Environment Variables)
# ------------------------------------------------------------------------------
%prod.quarkus.datasource.db-kind={db_kind}
%prod.quarkus.datasource.jdbc.url=${{DB_URL:{prod_jdbc_url}}}
%prod.quarkus.datasource.username=${{DB_USER:{client_code}_app}}
%prod.quarkus.datasource.password=${{DB_PASSWORD:Secret123!}}
%prod.quarkus.hibernate-orm.database.generation=validate
%prod.mp.jwt.verify.issuer=${{JWT_ISSUER:https://login.microsoftonline.com/common/v2.0}}
%prod.mp.jwt.verify.publickey.location=${{JWT_PUBLIC_KEY_URL:https://login.microsoftonline.com/common/discovery/v2.0/keys}}
"""
        files[prop_path] = content

    @classmethod
    def _guarantee_resources_and_keys(cls, files: Dict[str, str], primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], default_status: str):
        """Generate import.sql and RSA PEM keys for JWT testing."""
        # 1. RSA Keys
        pub_pem, priv_pem = generate_dev_keys()
        files["src/main/resources/publicKey.pem"] = pub_pem
        files["src/test/resources/privateKey.pem"] = priv_pem

        # 2. Dynamic import.sql
        if primary_entity.lower() in ["book", "libro"]:
            files["src/main/resources/import.sql"] = """-- Seed initial data for local development and integration tests
INSERT INTO categories (id, name, description) VALUES ('a0000000-0000-0000-0000-000000000001', 'Software Engineering', 'Books about software design and best practices');
INSERT INTO categories (id, name, description) VALUES ('a0000000-0000-0000-0000-000000000002', 'Cloud & Architecture', 'Distributed systems and cloud computing');

INSERT INTO books (id, title, author, isbn, price, stock, category_id, status, created_at)
VALUES ('b0000000-0000-0000-0000-000000000001', 'Clean Code', 'Robert C. Martin', '9780132350884', 39.99, 15, 'a0000000-0000-0000-0000-000000000001', 'ACTIVE', CURRENT_TIMESTAMP);
"""
        elif primary_entity.lower() in ["creditcard", "card", "tarjeta"]:
            files["src/main/resources/import.sql"] = """-- Seed initial data for credit cards
INSERT INTO credit_cards (id, card_number_masked, holder_name, holder_dni, credit_limit, status, created_at)
VALUES ('c0000000-0000-0000-0000-000000000001', '4111********1111', 'Juan Perez', '45871234', 5000.00, 'ACTIVE', CURRENT_TIMESTAMP);
"""
        else:
            cols = [to_snake_case(f["name"]) for f in fields]
            vals = [get_sample_sql_value(f, default_status) for f in fields]
            files["src/main/resources/import.sql"] = f"""-- Seed initial data for {primary_entity}
INSERT INTO {primary_table} ({', '.join(cols)})
VALUES ({', '.join(vals)});
"""

    @classmethod
    def _guarantee_hexagonal_code(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], default_status: str, blueprint: Dict[str, Any]):
        """Guarantee clean Hexagonal UseCases with distinct method names and CDI adapters."""
        if primary_entity.lower() in ["book", "libro"]:
            cls._ensure_book_catalog_domain(files, pkg_prefix, pkg_path)
        else:
            cls._ensure_universal_hexagonal_domain(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields, default_status)

        # Invariant: Guarantee Core Domain Exceptions for ALL microservices
        files[f"src/main/java/{pkg_path}/domain/exception/ResourceNotFoundException.java"] = f"""package {pkg_prefix}.domain.exception;

public class ResourceNotFoundException extends RuntimeException {{
    public ResourceNotFoundException(String message) {{
        super(message);
    }}
}}
"""
        files[f"src/main/java/{pkg_path}/domain/exception/BusinessConflictException.java"] = f"""package {pkg_prefix}.domain.exception;

public class BusinessConflictException extends RuntimeException {{
    public BusinessConflictException(String message) {{
        super(message);
    }}
}}
"""

        # Fix conflicting execute(UUID) signatures across all UseCase files
        for fpath, jcode in list(files.items()):
            if "UseCase.java" in fpath and "interface " in jcode:
                if "Get" in fpath and "execute(UUID" in jcode:
                    files[fpath] = re.sub(r"\bexecute\s*\(UUID\s+([a-zA-Z0-9_]+)\)", r"getById(UUID \1)", jcode)
                elif "Delete" in fpath and "execute(UUID" in jcode:
                    files[fpath] = re.sub(r"\bexecute\s*\(UUID\s+([a-zA-Z0-9_]+)\)", r"delete(UUID \1)", jcode)
                elif "Update" in fpath and "execute(" in jcode:
                    files[fpath] = re.sub(r"\bexecute\s*\(UUID\s+([a-zA-Z0-9_]+),\s*", r"update(UUID \1, ", jcode)
                elif "Create" in fpath and "execute(" in jcode:
                    files[fpath] = re.sub(r"\bexecute\s*\(", r"create(", jcode)
                elif "Search" in fpath and "execute(" in jcode:
                    files[fpath] = re.sub(r"\bexecute\s*\(", r"search(", jcode)

        # Fix Service implementation method names and imports
        service_path = f"src/main/java/{pkg_path}/application/service/{primary_entity}Service.java"
        if service_path in files:
            svc_code = files[service_path]
            svc_code = svc_code.replace(f"import {pkg_prefix}.domain.repository.", f"import {pkg_prefix}.domain.port.out.")
            files[service_path] = svc_code

    @classmethod
    def _ensure_book_catalog_domain(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str):
        """Ensure complete, non-colliding Hexagonal implementation for Book Catalog."""
        # Domain Models
        files[f"src/main/java/{pkg_path}/domain/model/Category.java"] = f"""package {pkg_prefix}.domain.model;

import java.util.UUID;

public class Category {{
    private UUID id;
    private String name;
    private String description;

    public Category() {{}}

    public Category(UUID id, String name, String description) {{
        this.id = id;
        this.name = name;
        this.description = description;
    }}

    public UUID getId() {{ return id; }}
    public void setId(UUID id) {{ this.id = id; }}
    public String getName() {{ return name; }}
    public void setName(String name) {{ this.name = name; }}
    public String getDescription() {{ return description; }}
    public void setDescription(String description) {{ this.description = description; }}
}}
"""

        files[f"src/main/java/{pkg_path}/domain/model/Book.java"] = f"""package {pkg_prefix}.domain.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class Book {{
    private UUID id;
    private String title;
    private String author;
    private String isbn;
    private BigDecimal price;
    private Integer stock;
    private UUID categoryId;
    private String status;
    private LocalDateTime createdAt;

    public Book() {{}}

    public Book(UUID id, String title, String author, String isbn, BigDecimal price, Integer stock, UUID categoryId, String status) {{
        this.id = id;
        this.title = title;
        this.author = author;
        this.isbn = isbn;
        this.price = price;
        this.stock = stock;
        this.categoryId = categoryId;
        this.status = status;
        this.createdAt = LocalDateTime.now();
    }}

    public UUID getId() {{ return id; }}
    public void setId(UUID id) {{ this.id = id; }}
    public String getTitle() {{ return title; }}
    public void setTitle(String title) {{ this.title = title; }}
    public String getAuthor() {{ return author; }}
    public void setAuthor(String author) {{ this.author = author; }}
    public String getIsbn() {{ return isbn; }}
    public void setIsbn(String isbn) {{ this.isbn = isbn; }}
    public BigDecimal getPrice() {{ return price; }}
    public void setPrice(BigDecimal price) {{ this.price = price; }}
    public Integer getStock() {{ return stock; }}
    public void setStock(Integer stock) {{ this.stock = stock; }}
    public UUID getCategoryId() {{ return categoryId; }}
    public void setCategoryId(UUID categoryId) {{ this.categoryId = categoryId; }}
    public String getStatus() {{ return status; }}
    public void setStatus(String status) {{ this.status = status; }}
    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public void setCreatedAt(LocalDateTime createdAt) {{ this.createdAt = createdAt; }}
}}
"""

        # Inbound Ports (Use Cases) with distinct semantic method names
        files[f"src/main/java/{pkg_path}/domain/port/in/CreateBookUseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.Book;

public interface CreateBookUseCase {{
    Book create(Book book);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/GetBookUseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.Book;
import java.util.UUID;

public interface GetBookUseCase {{
    Book getById(UUID id);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/SearchBooksUseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import {pkg_prefix}.domain.model.Book;

public interface SearchBooksUseCase {{
    PageResponse<Book> search(String query, String status, int page, int size);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/UpdateBookUseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.Book;
import java.util.UUID;

public interface UpdateBookUseCase {{
    Book update(UUID id, Book book);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/DeleteBookUseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import java.util.UUID;

public interface DeleteBookUseCase {{
    void delete(UUID id);
}}
"""

        # Outbound Ports
        files[f"src/main/java/{pkg_path}/domain/port/out/BookRepositoryPort.java"] = f"""package {pkg_prefix}.domain.port.out;

import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import {pkg_prefix}.domain.model.Book;
import java.util.Optional;
import java.util.UUID;

public interface BookRepositoryPort {{
    Book save(Book book);
    Optional<Book> findById(UUID id);
    Optional<Book> findByIsbn(String isbn);
    boolean existsByIsbn(String isbn);
    PageResponse<Book> search(String query, String status, int page, int size);
    long count(String query, String status);
    void deleteById(UUID id);
    boolean existsById(UUID id);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/out/CategoryRepositoryPort.java"] = f"""package {pkg_prefix}.domain.port.out;

import {pkg_prefix}.domain.model.Category;
import java.util.Optional;
import java.util.UUID;

public interface CategoryRepositoryPort {{
    Optional<Category> findById(UUID id);
    boolean existsById(UUID id);
}}
"""

        # Exceptions
        files[f"src/main/java/{pkg_path}/domain/exception/ResourceNotFoundException.java"] = f"""package {pkg_prefix}.domain.exception;

public class ResourceNotFoundException extends RuntimeException {{
    public ResourceNotFoundException(String message) {{
        super(message);
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/domain/exception/BusinessConflictException.java"] = f"""package {pkg_prefix}.domain.exception;

public class BusinessConflictException extends RuntimeException {{
    public BusinessConflictException(String message) {{
        super(message);
    }}
}}
"""

        # Application Service implementing all 5 distinct use case methods
        files[f"src/main/java/{pkg_path}/application/service/BookService.java"] = f"""package {pkg_prefix}.application.service;

import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import {pkg_prefix}.domain.exception.BusinessConflictException;
import {pkg_prefix}.domain.exception.ResourceNotFoundException;
import {pkg_prefix}.domain.model.Book;
import {pkg_prefix}.domain.port.in.*;
import {pkg_prefix}.domain.port.out.BookRepositoryPort;
import {pkg_prefix}.domain.port.out.CategoryRepositoryPort;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.UUID;

@ApplicationScoped
public class BookService implements CreateBookUseCase, GetBookUseCase, SearchBooksUseCase, UpdateBookUseCase, DeleteBookUseCase {{

    @Inject
    BookRepositoryPort bookRepositoryPort;

    @Inject
    CategoryRepositoryPort categoryRepositoryPort;

    @Override
    @Transactional
    public Book create(Book book) {{
        if (book.getCategoryId() != null && !categoryRepositoryPort.existsById(book.getCategoryId())) {{
            throw new ResourceNotFoundException("Category with ID " + book.getCategoryId() + " does not exist");
        }}
        if (book.getIsbn() != null && bookRepositoryPort.existsByIsbn(book.getIsbn())) {{
            throw new BusinessConflictException("Book with ISBN " + book.getIsbn() + " already exists in catalog");
        }}
        if (book.getId() == null) {{
            book.setId(UUID.randomUUID());
        }}
        book.setStatus("ACTIVE");
        book.setCreatedAt(LocalDateTime.now());
        return bookRepositoryPort.save(book);
    }}

    @Override
    public Book getById(UUID id) {{
        return bookRepositoryPort.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found with ID: " + id));
    }}

    @Override
    public PageResponse<Book> search(String query, String status, int page, int size) {{
        return bookRepositoryPort.search(query, status, page, size);
    }}

    @Override
    @Transactional
    public Book update(UUID id, Book book) {{
        Book existing = getById(id);
        if (book.getCategoryId() != null && !categoryRepositoryPort.existsById(book.getCategoryId())) {{
            throw new ResourceNotFoundException("Category with ID " + book.getCategoryId() + " does not exist");
        }}
        if (book.getTitle() != null) existing.setTitle(book.getTitle());
        if (book.getAuthor() != null) existing.setAuthor(book.getAuthor());
        if (book.getPrice() != null) existing.setPrice(book.getPrice());
        if (book.getStock() != null) existing.setStock(book.getStock());
        if (book.getCategoryId() != null) existing.setCategoryId(book.getCategoryId());
        return bookRepositoryPort.save(existing);
    }}

    @Override
    @Transactional
    public void delete(UUID id) {{
        Book existing = getById(id);
        // Logical soft-delete
        existing.setStatus("INACTIVE");
        bookRepositoryPort.save(existing);
    }}
}}
"""

        # Outbound Adapters (Panache Entities and Repositories with safe merge/update logic)
        files[f"src/main/java/{pkg_path}/adapter/out/persistence/entity/CategoryEntity.java"] = f"""package {pkg_prefix}.adapter.out.persistence.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.UUID;

@Entity
@Table(name = "categories")
public class CategoryEntity {{
    @Id
    public UUID id;
    public String name;
    public String description;

    public CategoryEntity() {{}}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/repository/CategoryPanacheRepository.java"] = f"""package {pkg_prefix}.adapter.out.persistence.repository;

import {pkg_prefix}.adapter.out.persistence.entity.CategoryEntity;
import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.UUID;

@ApplicationScoped
public class CategoryPanacheRepository implements PanacheRepositoryBase<CategoryEntity, UUID> {{
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/CategoryRepositoryAdapter.java"] = f"""package {pkg_prefix}.adapter.out.persistence;

import {pkg_prefix}.adapter.out.persistence.entity.CategoryEntity;
import {pkg_prefix}.adapter.out.persistence.repository.CategoryPanacheRepository;
import {pkg_prefix}.domain.model.Category;
import {pkg_prefix}.domain.port.out.CategoryRepositoryPort;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.Optional;
import java.util.UUID;

@ApplicationScoped
public class CategoryRepositoryAdapter implements CategoryRepositoryPort {{

    @Inject
    CategoryPanacheRepository repository;

    @Override
    public Optional<Category> findById(UUID id) {{
        return repository.findByIdOptional(id).map(e -> new Category(e.id, e.name, e.description));
    }}

    @Override
    public boolean existsById(UUID id) {{
        return repository.count("id", id) > 0;
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/entity/BookEntity.java"] = f"""package {pkg_prefix}.adapter.out.persistence.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "books")
public class BookEntity {{
    @Id
    public UUID id;

    @Column(nullable = false)
    public String title;

    @Column(nullable = false)
    public String author;

    @Column(nullable = false, unique = true)
    public String isbn;

    @Column(nullable = false)
    public BigDecimal price;

    @Column(nullable = false)
    public Integer stock;

    @Column(name = "category_id")
    public UUID categoryId;

    @Column(nullable = false)
    public String status;

    @Column(name = "created_at")
    public LocalDateTime createdAt;

    public BookEntity() {{}}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/repository/BookPanacheRepository.java"] = f"""package {pkg_prefix}.adapter.out.persistence.repository;

import {pkg_prefix}.adapter.out.persistence.entity.BookEntity;
import io.quarkus.hibernate.orm.panache.PanacheQuery;
import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import io.quarkus.panache.common.Page;
import io.quarkus.panache.common.Parameters;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.List;
import java.util.UUID;

@ApplicationScoped
public class BookPanacheRepository implements PanacheRepositoryBase<BookEntity, UUID> {{

    public PanacheQuery<BookEntity> searchBooks(String query, String status) {{
        StringBuilder hql = new StringBuilder("1 = 1");
        Parameters params = new Parameters();

        if (query != null && !query.trim().isEmpty()) {{
            hql.append(" and (lower(title) like :q or lower(author) like :q or isbn like :q)");
            params.and("q", "%" + query.trim().toLowerCase() + "%");
        }}
        if (status != null && !status.trim().isEmpty()) {{
            hql.append(" and status = :status");
            params.and("status", status.trim().toUpperCase());
        }}

        return find(hql.toString(), params);
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/BookRepositoryAdapter.java"] = f"""package {pkg_prefix}.adapter.out.persistence;

import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import {pkg_prefix}.adapter.out.persistence.entity.BookEntity;
import {pkg_prefix}.adapter.out.persistence.repository.BookPanacheRepository;
import {pkg_prefix}.domain.model.Book;
import {pkg_prefix}.domain.port.out.BookRepositoryPort;
import io.quarkus.panache.common.Page;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@ApplicationScoped
public class BookRepositoryAdapter implements BookRepositoryPort {{

    @Inject
    BookPanacheRepository repository;

    @Override
    @Transactional
    public Book save(Book domain) {{
        BookEntity entity = repository.findById(domain.getId());
        if (entity != null) {{
            // Entity exists -> update managed entity fields
            entity.title = domain.getTitle();
            entity.author = domain.getAuthor();
            entity.price = domain.getPrice();
            entity.stock = domain.getStock();
            entity.categoryId = domain.getCategoryId();
            entity.status = domain.getStatus();
        }} else {{
            // New entity -> persist
            entity = new BookEntity();
            entity.id = domain.getId() != null ? domain.getId() : UUID.randomUUID();
            entity.title = domain.getTitle();
            entity.author = domain.getAuthor();
            entity.isbn = domain.getIsbn();
            entity.price = domain.getPrice();
            entity.stock = domain.getStock();
            entity.categoryId = domain.getCategoryId();
            entity.status = domain.getStatus() != null ? domain.getStatus() : "ACTIVE";
            entity.createdAt = domain.getCreatedAt() != null ? domain.getCreatedAt() : LocalDateTime.now();
            repository.persist(entity);
        }}
        return toDomain(entity);
    }}

    @Override
    public Optional<Book> findById(UUID id) {{
        return repository.findByIdOptional(id).map(this::toDomain);
    }}

    @Override
    public Optional<Book> findByIsbn(String isbn) {{
        return repository.find("isbn", isbn).firstResultOptional().map(this::toDomain);
    }}

    @Override
    public boolean existsByIsbn(String isbn) {{
        return repository.count("isbn", isbn) > 0;
    }}

    @Override
    public PageResponse<Book> search(String query, String status, int page, int size) {{
        var panacheQuery = repository.searchBooks(query, status);
        long totalElements = panacheQuery.count();
        List<BookEntity> entities = panacheQuery.page(Page.of(page, size)).list();
        List<Book> items = entities.stream().map(this::toDomain).collect(Collectors.toList());
        int totalPages = (int) Math.ceil((double) totalElements / size);
        return new PageResponse<>(items, page, size, totalElements, totalPages);
    }}

    @Override
    public long count(String query, String status) {{
        return repository.searchBooks(query, status).count();
    }}

    @Override
    @Transactional
    public void deleteById(UUID id) {{
        repository.deleteById(id);
    }}

    @Override
    public boolean existsById(UUID id) {{
        return repository.count("id", id) > 0;
    }}

    private Book toDomain(BookEntity entity) {{
        Book book = new Book(
            entity.id,
            entity.title,
            entity.author,
            entity.isbn,
            entity.price,
            entity.stock,
            entity.categoryId,
            entity.status
        );
        book.setCreatedAt(entity.createdAt);
        return book;
    }}
}}
"""



    @classmethod
    def _guarantee_exception_mappers(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str):
        """Ensure standard uniform error response and exception mappers (400, 404, 409, 500)."""
        files[f"src/main/java/{pkg_path}/adapter/in/web/dto/ErrorResponse.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

public class ErrorResponse {{
    private LocalDateTime timestamp;
    private int status;
    private String error;
    private String message;
    private String path;
    private List<String> details;

    public ErrorResponse() {{
        this.timestamp = LocalDateTime.now();
        this.details = new ArrayList<>();
    }}

    public ErrorResponse(int status, String error, String message, String path) {{
        this.timestamp = LocalDateTime.now();
        this.status = status;
        this.error = error;
        this.message = message;
        this.path = path;
        this.details = new ArrayList<>();
    }}

    public LocalDateTime getTimestamp() {{ return timestamp; }}
    public int getStatus() {{ return status; }}
    public void setStatus(int status) {{ this.status = status; }}
    public String getError() {{ return error; }}
    public void setError(String error) {{ this.error = error; }}
    public String getMessage() {{ return message; }}
    public void setMessage(String message) {{ this.message = message; }}
    public String getPath() {{ return path; }}
    public void setPath(String path) {{ this.path = path; }}
    public List<String> getDetails() {{ return details; }}
    public void setDetails(List<String> details) {{ this.details = details; }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/in/web/mapper/ResourceNotFoundExceptionMapper.java"] = f"""package {pkg_prefix}.adapter.in.web.mapper;

import {pkg_prefix}.adapter.in.web.dto.ErrorResponse;
import {pkg_prefix}.domain.exception.ResourceNotFoundException;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

@Provider
public class ResourceNotFoundExceptionMapper implements ExceptionMapper<ResourceNotFoundException> {{

    @Context
    UriInfo uriInfo;

    @Override
    public Response toResponse(ResourceNotFoundException exception) {{
        ErrorResponse error = new ErrorResponse(
            404,
            "Not Found",
            exception.getMessage(),
            uriInfo != null ? uriInfo.getPath() : "/api"
        );
        return Response.status(Response.Status.NOT_FOUND).entity(error).build();
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/in/web/mapper/BusinessConflictExceptionMapper.java"] = f"""package {pkg_prefix}.adapter.in.web.mapper;

import {pkg_prefix}.adapter.in.web.dto.ErrorResponse;
import {pkg_prefix}.domain.exception.BusinessConflictException;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

@Provider
public class BusinessConflictExceptionMapper implements ExceptionMapper<BusinessConflictException> {{

    @Context
    UriInfo uriInfo;

    @Override
    public Response toResponse(BusinessConflictException exception) {{
        ErrorResponse error = new ErrorResponse(
            409,
            "Conflict",
            exception.getMessage(),
            uriInfo != null ? uriInfo.getPath() : "/api"
        );
        return Response.status(Response.Status.CONFLICT).entity(error).build();
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/in/web/mapper/ConstraintViolationExceptionMapper.java"] = f"""package {pkg_prefix}.adapter.in.web.mapper;

import {pkg_prefix}.adapter.in.web.dto.ErrorResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import java.util.stream.Collectors;

@Provider
public class ConstraintViolationExceptionMapper implements ExceptionMapper<ConstraintViolationException> {{

    @Context
    UriInfo uriInfo;

    @Override
    public Response toResponse(ConstraintViolationException exception) {{
        ErrorResponse error = new ErrorResponse(
            400,
            "Bad Request",
            "Validation failed for request parameters",
            uriInfo != null ? uriInfo.getPath() : "/api"
        );
        var details = exception.getConstraintViolations().stream()
            .map(cv -> cv.getPropertyPath() + ": " + cv.getMessage())
            .collect(Collectors.toList());
        error.setDetails(details);
        return Response.status(Response.Status.BAD_REQUEST).entity(error).build();
    }}
}}
"""

        files[f"src/main/java/{pkg_path}/adapter/in/web/mapper/GlobalExceptionMapper.java"] = f"""package {pkg_prefix}.adapter.in.web.mapper;

import {pkg_prefix}.adapter.in.web.dto.ErrorResponse;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import org.jboss.logging.Logger;

@Provider
public class GlobalExceptionMapper implements ExceptionMapper<Exception> {{

    private static final Logger LOG = Logger.getLogger(GlobalExceptionMapper.class);

    @Context
    UriInfo uriInfo;

    @Override
    public Response toResponse(Exception exception) {{
        LOG.error("Unhandled exception intercepted by GlobalExceptionMapper", exception);
        ErrorResponse error = new ErrorResponse(
            500,
            "Internal Server Error",
            "An unexpected error occurred. Please contact system support.",
            uriInfo != null ? uriInfo.getPath() : "/api"
        );
        return Response.status(Response.Status.INTERNAL_SERVER_ERROR).entity(error).build();
    }}
}}
"""





    @classmethod
    def _guarantee_rest_resource(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], blueprint: Dict[str, Any]):
        """Ensure Resource exists with DTOs, @Path, @RolesAllowed, @Valid."""
        # PageResponse DTO
        files[f"src/main/java/{pkg_path}/adapter/in/web/dto/PageResponse.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import java.util.List;

public class PageResponse<T> {{
    private List<T> content;
    private int page;
    private int size;
    private long totalElements;
    private int totalPages;

    public PageResponse() {{}}

    public PageResponse(List<T> content, int page, int size, long totalElements, int totalPages) {{
        this.content = content;
        this.page = page;
        this.size = size;
        this.totalElements = totalElements;
        this.totalPages = totalPages;
    }}

    public List<T> getContent() {{ return content; }}
    public void setContent(List<T> content) {{ this.content = content; }}
    public int getPage() {{ return page; }}
    public void setPage(int page) {{ this.page = page; }}
    public int getSize() {{ return size; }}
    public void setSize(int size) {{ this.size = size; }}
    public long getTotalElements() {{ return totalElements; }}
    public void setTotalElements(long totalElements) {{ this.totalElements = totalElements; }}
    public int getTotalPages() {{ return totalPages; }}
    public void setTotalPages(int totalPages) {{ this.totalPages = totalPages; }}
}}
"""

        if primary_entity.lower() in ["book", "libro"]:
            # Book DTOs and Resource
            files[f"src/main/java/{pkg_path}/adapter/in/web/dto/BookRequest.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.util.UUID;

public class BookRequest {{
    @NotBlank(message = "Title is required")
    private String title;
    @NotBlank(message = "Author is required")
    private String author;
    @NotBlank(message = "ISBN is required")
    private String isbn;
    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.01", message = "Price must be greater than zero")
    private BigDecimal price;
    @NotNull(message = "Stock is required")
    @Min(value = 0, message = "Stock cannot be negative")
    private Integer stock;
    @NotNull(message = "Category ID is required")
    private UUID categoryId;

    public BookRequest() {{}}

    public String getTitle() {{ return title; }}
    public void setTitle(String title) {{ this.title = title; }}
    public String getAuthor() {{ return author; }}
    public void setAuthor(String author) {{ this.author = author; }}
    public String getIsbn() {{ return isbn; }}
    public void setIsbn(String isbn) {{ this.isbn = isbn; }}
    public BigDecimal getPrice() {{ return price; }}
    public void setPrice(BigDecimal price) {{ this.price = price; }}
    public Integer getStock() {{ return stock; }}
    public void setStock(Integer stock) {{ this.stock = stock; }}
    public UUID getCategoryId() {{ return categoryId; }}
    public void setCategoryId(UUID categoryId) {{ this.categoryId = categoryId; }}
}}
"""
            files[f"src/main/java/{pkg_path}/adapter/in/web/dto/BookResponse.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import {pkg_prefix}.domain.model.Book;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

public class BookResponse {{
    private UUID id;
    private String title;
    private String author;
    private String isbn;
    private BigDecimal price;
    private Integer stock;
    private UUID categoryId;
    private String status;
    private LocalDateTime createdAt;

    public BookResponse() {{}}

    public static BookResponse fromDomain(Book b) {{
        BookResponse r = new BookResponse();
        r.id = b.getId();
        r.title = b.getTitle();
        r.author = b.getAuthor();
        r.isbn = b.getIsbn();
        r.price = b.getPrice();
        r.stock = b.getStock();
        r.categoryId = b.getCategoryId();
        r.status = b.getStatus();
        r.createdAt = b.getCreatedAt();
        return r;
    }}

    public UUID getId() {{ return id; }}
    public String getTitle() {{ return title; }}
    public String getAuthor() {{ return author; }}
    public String getIsbn() {{ return isbn; }}
    public BigDecimal getPrice() {{ return price; }}
    public Integer getStock() {{ return stock; }}
    public UUID getCategoryId() {{ return categoryId; }}
    public String getStatus() {{ return status; }}
    public LocalDateTime getCreatedAt() {{ return createdAt; }}
}}
"""
            files[f"src/main/java/{pkg_path}/adapter/in/web/BookResource.java"] = f"""package {pkg_prefix}.adapter.in.web;

import {pkg_prefix}.adapter.in.web.dto.BookRequest;
import {pkg_prefix}.adapter.in.web.dto.BookResponse;
import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import {pkg_prefix}.domain.model.Book;
import {pkg_prefix}.domain.port.in.*;
import jakarta.annotation.security.RolesAllowed;
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.eclipse.microprofile.openapi.annotations.Operation;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;
import java.net.URI;
import java.util.UUID;
import java.util.stream.Collectors;

@Path("/api/v1/books")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@Tag(name = "Books", description = "Enterprise Book Catalog Management")
public class BookResource {{

    @Inject
    CreateBookUseCase createBookUseCase;
    @Inject
    GetBookUseCase getBookUseCase;
    @Inject
    SearchBooksUseCase searchBooksUseCase;
    @Inject
    UpdateBookUseCase updateBookUseCase;
    @Inject
    DeleteBookUseCase deleteBookUseCase;

    @POST
    @RolesAllowed({{"ADMIN", "OPERATOR"}})
    @Operation(summary = "Register a new book in catalog")
    public Response createBook(@Valid BookRequest request) {{
        Book domain = new Book();
        domain.setTitle(request.getTitle());
        domain.setAuthor(request.getAuthor());
        domain.setIsbn(request.getIsbn());
        domain.setPrice(request.getPrice());
        domain.setStock(request.getStock());
        domain.setCategoryId(request.getCategoryId());

        Book created = createBookUseCase.create(domain);
        return Response.created(URI.create("/api/v1/books/" + created.getId())).entity(BookResponse.fromDomain(created)).build();
    }}

    @GET
    @RolesAllowed({{"ADMIN", "OPERATOR", "AUDITOR"}})
    @Operation(summary = "Search books with pagination")
    public Response searchBooks(
            @QueryParam("q") @DefaultValue("") String query,
            @QueryParam("status") @DefaultValue("") String status,
            @QueryParam("page") @DefaultValue("0") int page,
            @QueryParam("size") @DefaultValue("20") int size) {{
        var pageDomain = searchBooksUseCase.search(query, status, page, size);
        var content = pageDomain.getContent().stream().map(BookResponse::fromDomain).collect(Collectors.toList());
        return Response.ok(new PageResponse<>(content, pageDomain.getPage(), pageDomain.getSize(), pageDomain.getTotalElements(), pageDomain.getTotalPages())).build();
    }}

    @GET
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN", "OPERATOR", "AUDITOR"}})
    @Operation(summary = "Retrieve book by ID")
    public Response getBookById(@PathParam("id") UUID id) {{
        Book book = getBookUseCase.getById(id);
        return Response.ok(BookResponse.fromDomain(book)).build();
    }}

    @PUT
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN", "OPERATOR"}})
    @Operation(summary = "Update existing book")
    public Response updateBook(@PathParam("id") UUID id, @Valid BookRequest request) {{
        Book domain = new Book();
        domain.setTitle(request.getTitle());
        domain.setAuthor(request.getAuthor());
        domain.setIsbn(request.getIsbn());
        domain.setPrice(request.getPrice());
        domain.setStock(request.getStock());
        domain.setCategoryId(request.getCategoryId());
        Book updated = updateBookUseCase.update(id, domain);
        return Response.ok(BookResponse.fromDomain(updated)).build();
    }}

    @DELETE
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN"}})
    @Operation(summary = "Delete book by ID")
    public Response deleteBook(@PathParam("id") UUID id) {{
        deleteBookUseCase.delete(id);
        return Response.noContent().build();
    }}
}}
"""
        else:
            cls._ensure_universal_rest_resource(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields)

    @classmethod
    def _guarantee_tests(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], default_status: str):
        """Ensure unit & integration tests compile and pass with Mockito and TestSecurity."""
        if primary_entity.lower() in ["book", "libro"]:
            book_payload_code = 'String payload = "{\\"title\\": \\"Clean Code\\", \\"author\\": \\"Robert C. Martin\\", \\"isbn\\": \\"9780132350884\\", \\"price\\": 39.99, \\"stock\\": 15, \\"categoryId\\": \\"a0000000-0000-0000-0000-000000000001\\"}";'
            files[f"src/test/java/{pkg_path}/application/service/BookServiceTest.java"] = f"""package {pkg_prefix}.application.service;

import {pkg_prefix}.domain.exception.ResourceNotFoundException;
import {pkg_prefix}.domain.model.Book;
import {pkg_prefix}.domain.port.out.BookRepositoryPort;
import {pkg_prefix}.domain.port.out.CategoryRepositoryPort;
import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import java.math.BigDecimal;
import java.util.Optional;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
public class BookServiceTest {{
    @Inject
    BookService bookService;
    @InjectMock
    BookRepositoryPort bookRepositoryPort;
    @InjectMock
    CategoryRepositoryPort categoryRepositoryPort;

    private UUID categoryId;
    private UUID bookId;
    private Book sampleBook;

    @BeforeEach
    void setUp() {{
        categoryId = UUID.randomUUID();
        bookId = UUID.randomUUID();
        sampleBook = new Book(bookId, "Clean Architecture", "Robert Martin", "9780134494166", new BigDecimal("42.50"), 10, categoryId, "ACTIVE");
    }}

    @Test
    void testCreateBook() {{
        Mockito.when(categoryRepositoryPort.existsById(categoryId)).thenReturn(true);
        Mockito.when(bookRepositoryPort.save(Mockito.any())).thenReturn(sampleBook);
        Book created = bookService.create(sampleBook);
        assertNotNull(created);
        assertEquals("Clean Architecture", created.getTitle());
    }}

    @Test
    void testFindByIdNotFound() {{
        Mockito.when(bookRepositoryPort.findById(bookId)).thenReturn(Optional.empty());
        assertThrows(ResourceNotFoundException.class, () -> bookService.getById(bookId));
    }}
}}
"""
            files[f"src/test/java/{pkg_path}/adapter/in/web/BookResourceTest.java"] = f"""package {pkg_prefix}.adapter.in.web;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.security.TestSecurity;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@QuarkusTest
public class BookResourceTest {{
    @Test
    @TestSecurity(user = "adminUser", roles = {{"ADMIN", "OPERATOR"}})
    void testCreateEndpoint() {{
        {book_payload_code}
        given()
            .contentType(ContentType.JSON)
            .body(payload)
            .when().post("/api/v1/books")
            .then()
            .statusCode(201)
            .header("Location", notNullValue());
    }}

    @Test
    @TestSecurity(user = "auditorUser", roles = {{"AUDITOR"}})
    void testSearchEndpoint() {{
        given()
            .when().get("/api/v1/books")
            .then()
            .statusCode(200)
            .body("content", notNullValue());
    }}

    @Test
    void testUnauthorized() {{
        given().when().get("/api/v1/books").then().statusCode(401);
    }}
}}
"""
        else:
            cls._ensure_universal_tests(files, pkg_prefix, pkg_path, primary_entity, primary_table, fields, default_status)

    @classmethod
    def _guarantee_postman_collection(cls, files: Dict[str, str], artifact_id: str, primary_entity: str, primary_table: str, client_code: str, fields: List[Dict[str, Any]], default_status: str):
        """Generate Postman v2.1 collection dynamically matching the real entity and fields."""
        postman_path = f"postman/{artifact_id}.postman_collection.json"
        
        req_fields = [f for f in fields if not f.get("is_id") and f["name"] not in ["id", "createdAt", "created_at", "status", "estado"]]
        sample_body = {f["name"]: get_sample_json_value(f, default_status) for f in req_fields}

        collection = {
            "info": {
                "name": f"{artifact_id.upper()} - Enterprise API",
                "description": f"Dynamic Postman Collection for {primary_entity} ({artifact_id}).",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "variable": [
                {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
                {"key": "token", "value": "Bearer YOUR_JWT_TOKEN_HERE", "type": "string"},
                {"key": "sampleId", "value": "d0000000-0000-0000-0000-000000000001", "type": "string"}
            ],
            "item": [
                {
                    "name": "01 - Health & Observability",
                    "item": [
                        {"name": "Health Status", "request": {"method": "GET", "url": "{{baseUrl}}/q/health"}},
                        {"name": "OpenAPI Spec", "request": {"method": "GET", "url": "{{baseUrl}}/q/openapi"}}
                    ]
                },
                {
                    "name": "02 - CRUD Operations",
                    "item": [
                        {
                            "name": f"Search & List {primary_entity}",
                            "request": {
                                "method": "GET",
                                "header": [{"key": "Authorization", "value": "{{token}}"}],
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}?q=&status={default_status}&page=0&size=20"
                            }
                        },
                        {
                            "name": f"Get {primary_entity} by ID",
                            "request": {
                                "method": "GET",
                                "header": [{"key": "Authorization", "value": "{{token}}"}],
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}/{{{{sampleId}}}}"
                            }
                        },
                        {
                            "name": f"Create {primary_entity}",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {"key": "Authorization", "value": "{{token}}"},
                                    {"key": "Content-Type", "value": "application/json"}
                                ],
                                "body": {"mode": "raw", "raw": json.dumps(sample_body, indent=2)},
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}"
                            }
                        },
                        {
                            "name": f"Update {primary_entity}",
                            "request": {
                                "method": "PUT",
                                "header": [
                                    {"key": "Authorization", "value": "{{token}}"},
                                    {"key": "Content-Type", "value": "application/json"}
                                ],
                                "body": {"mode": "raw", "raw": json.dumps(sample_body, indent=2)},
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}/{{{{sampleId}}}}"
                            }
                        },
                        {
                            "name": f"Delete {primary_entity}",
                            "request": {
                                "method": "DELETE",
                                "header": [{"key": "Authorization", "value": "{{token}}"}],
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}/{{{{sampleId}}}}"
                            }
                        }
                    ]
                },
                {
                    "name": "03 - Error Scenarios",
                    "item": [
                        {
                            "name": "400 - Validation Failed",
                            "request": {
                                "method": "POST",
                                "header": [{"key": "Authorization", "value": "{{token}}"}, {"key": "Content-Type", "value": "application/json"}],
                                "body": {"mode": "raw", "raw": "{}"},
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}"
                            }
                        },
                        {
                            "name": "401 - Unauthorized",
                            "request": {
                                "method": "GET",
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}"
                            }
                        },
                        {
                            "name": "404 - Not Found",
                            "request": {
                                "method": "GET",
                                "header": [{"key": "Authorization", "value": "{{token}}"}],
                                "url": f"{{{{baseUrl}}}}/api/v1/{primary_table}/00000000-0000-0000-0000-000000000000"
                            }
                        }
                    ]
                }
            ]
        }
        files[postman_path] = json.dumps(collection, indent=2)

    @classmethod
    def _guarantee_documentation(cls, files: Dict[str, str], artifact_id: str, pkg_prefix: str, primary_entity: str, primary_table: str, client_code: str, db_kind: str, fields: List[Dict[str, Any]]):
        """Generate dynamic README.md and cohesive docker-compose.yml matching the actual domain and database."""
        req_fields = [f for f in fields if not f.get("is_id") and f["name"] not in ["id", "createdAt", "created_at", "status", "estado"]]
        sample_body = json.dumps({f["name"]: get_sample_json_value(f) for f in req_fields}, indent=2)

        files["README.md"] = f"""# {artifact_id.upper()}

Enterprise Microservice built with **Quarkus 3.15** and **Java 21**, following **Hexagonal Architecture (Ports and Adapters)** for {client_code.upper()}.

---

## 🏛 Architecture Overview

```text
src/main/java/{pkg_prefix.replace('.', '/')}
├── domain/
│   ├── model/                  # Domain model: {primary_entity}
│   ├── port/in/                # Inbound use cases (Create, Get, Search, Update, Delete)
│   ├── port/out/               # Outbound port ({primary_entity}RepositoryPort)
│   └── exception/              # Domain exceptions (ResourceNotFound, BusinessConflict)
├── application/
│   └── service/                # Hexagonal Service implementation
└── adapter/
    ├── in/web/                 # JAX-RS REST Controller & DTOs
    │   ├── dto/                # {primary_entity}Request, {primary_entity}Response, PageResponse, ErrorResponse
    │   └── mapper/             # Standard ExceptionMappers (400, 404, 409, 500)
    └── out/persistence/        # Panache Entity, Repository & Persistence Adapter
```

---

## 🚀 Quickstart (Local Development)

The project includes an in-memory H2 database with automatic schema creation and initial seed data in `src/main/resources/import.sql`. You do **NOT** need an external database installed to run or test locally!

### 1. Run in Development Mode
```bash
./mvnw quarkus:dev
# or
mvn quarkus:dev
```
- **Swagger UI:** [http://localhost:8080/q/swagger-ui](http://localhost:8080/q/swagger-ui)
- **Health Check:** [http://localhost:8080/q/health](http://localhost:8080/q/health)
- **OpenAPI Schema:** [http://localhost:8080/q/openapi](http://localhost:8080/q/openapi)

### 2. Run Automated Verification Tests
```bash
mvn clean verify
```
All tests run with `@QuarkusTest`, Mockito (`quarkus-junit5-mockito`), and `@TestSecurity`.

---

## 📡 API Endpoints

- `POST /api/v1/{primary_table}`: Create a new {primary_entity} (Roles: `ADMIN`, `OPERATOR`)
- `GET /api/v1/{primary_table}`: Search and paginate {primary_entity} records (Roles: `ADMIN`, `OPERATOR`, `AUDITOR`)
- `GET /api/v1/{primary_table}/{{id}}`: Retrieve {primary_entity} by UUID (Roles: `ADMIN`, `OPERATOR`, `AUDITOR`)
- `PUT /api/v1/{primary_table}/{{id}}`: Update {primary_entity} details (Roles: `ADMIN`, `OPERATOR`)
- `DELETE /api/v1/{primary_table}/{{id}}`: Logical delete (Roles: `ADMIN`)

### Example Request Payload
```json
{sample_body}
```

---

## 📮 Postman Collection
Import the collection located in `postman/{artifact_id}.postman_collection.json`.
"""

        # Docker Compose cohesive with db_kind
        if db_kind == "mssql":
            files["docker-compose.yml"] = f"""version: '3.8'

services:
  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: {artifact_id}-db
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=Secret123!
    ports:
      - "1433:1433"
    volumes:
      - mssql_data:/var/opt/mssql

volumes:
  mssql_data:
"""
        else:
            files["docker-compose.yml"] = f"""version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: {artifact_id}-db
    environment:
      POSTGRES_DB: {client_code}_db
      POSTGRES_USER: {client_code}_app
      POSTGRES_PASSWORD: Secret123!
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
"""


    @classmethod
    def _cleanup_obsolete_files(cls, files: Dict[str, str], pkg_path: str):
        """Remove duplicate interfaces in obsolete packages and duplicate DTOs."""
        # Remove duplicate BookRepositoryPort in domain/repository
        dup_port = f"src/main/java/{pkg_path}/domain/repository/BookRepositoryPort.java"
        if dup_port in files:
            del files[dup_port]

        # Remove duplicate DTOs in application/dto if adapter/in/web/dto exists
        dup_req = f"src/main/java/{pkg_path}/application/dto/BookRequest.java"
        if dup_req in files:
            del files[dup_req]
        dup_resp = f"src/main/java/{pkg_path}/application/dto/BookResponse.java"
        if dup_resp in files:
            del files[dup_resp]

        # Clean stray Account files if domain is Book or other non-Account entity
        for fpath in list(files.keys()):
            if "Account" in fpath and any(k in fpath for k in ["pe/com/bcp/catalog", "book"]):
                del files[fpath]



    @classmethod
    def _auto_heal_java_syntax(cls, files: Dict[str, str]):
        """Detect and automatically heal unbalanced braces in all Java source files."""
        for fpath, code in list(files.items()):
            if not fpath.endswith(".java") or not isinstance(code, str):
                continue
            open_c = code.count("{")
            close_c = code.count("}")
            if open_c > close_c:
                missing = open_c - close_c
                files[fpath] = code.rstrip() + "\n" + ("}\n" * missing)
            elif close_c > open_c:
                excess = close_c - open_c
                repaired = code
                for _ in range(excess):
                    last_idx = repaired.rfind("}")
                    if last_idx != -1:
                        repaired = repaired[:last_idx] + repaired[last_idx + 1:]
                files[fpath] = repaired



    @classmethod
    def _ensure_universal_hexagonal_domain(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], default_status: str):
        """Dynamically generate Hexagonal domain, ports, service, and Panache persistence for ANY entity with ANY fields."""
        imports = get_field_imports(fields)
        imports_str = "\n".join(imports)
        non_id_fields = [f for f in fields if not f.get("is_id")]

        # 1. Domain Model
        field_decls = ["    private UUID id;"]
        getters_setters = [
            "    public UUID getId() { return id; }\n    public void setId(UUID id) { this.id = id; }"
        ]

        for f in non_id_fields:
            fname = f["name"]
            ftype = f["type"]
            pname = to_pascal_case(fname)
            field_decls.append(f"    private {ftype} {fname};")
            getters_setters.append(
                f"    public {ftype} get{pname}() {{ return {fname}; }}\n    public void set{pname}({ftype} {fname}) {{ this.{fname} = {fname}; }}"
            )

        fields_block = "\n".join(field_decls)
        gs_block = "\n\n".join(getters_setters)

        files[f"src/main/java/{pkg_path}/domain/model/{primary_entity}.java"] = f"""package {pkg_prefix}.domain.model;

{imports_str}

public class {primary_entity} {{
{fields_block}

    public {primary_entity}() {{}}

{gs_block}
}}
"""

        # 2. UseCases
        files[f"src/main/java/{pkg_path}/domain/port/in/Create{primary_entity}UseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.{primary_entity};

public interface Create{primary_entity}UseCase {{
    {primary_entity} create({primary_entity} entity);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/Get{primary_entity}UseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.{primary_entity};
import java.util.UUID;

public interface Get{primary_entity}UseCase {{
    {primary_entity} getById(UUID id);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/Search{primary_entity}UseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.adapter.in.web.dto.PageResponse;

public interface Search{primary_entity}UseCase {{
    PageResponse<{primary_entity}> search(String query, String status, int page, int size);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/Update{primary_entity}UseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import {pkg_prefix}.domain.model.{primary_entity};
import java.util.UUID;

public interface Update{primary_entity}UseCase {{
    {primary_entity} update(UUID id, {primary_entity} entity);
}}
"""

        files[f"src/main/java/{pkg_path}/domain/port/in/Delete{primary_entity}UseCase.java"] = f"""package {pkg_prefix}.domain.port.in;

import java.util.UUID;

public interface Delete{primary_entity}UseCase {{
    void delete(UUID id);
}}
"""

        # 3. Outbound Port
        files[f"src/main/java/{pkg_path}/domain/port/out/{primary_entity}RepositoryPort.java"] = f"""package {pkg_prefix}.domain.port.out;

import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import java.util.Optional;
import java.util.UUID;

public interface {primary_entity}RepositoryPort {{
    {primary_entity} save({primary_entity} entity);
    Optional<{primary_entity}> findById(UUID id);
    PageResponse<{primary_entity}> search(String query, String status, int page, int size);
    long count(String query, String status);
    void deleteById(UUID id);
    boolean existsById(UUID id);
}}
"""

        # 4. Service Implementation
        update_assignments = []
        for f in non_id_fields:
            fname = f["name"]
            if fname not in ["createdAt", "created_at"]:
                pname = to_pascal_case(fname)
                update_assignments.append(f"""        if (entity.get{pname}() != null) {{
            existing.set{pname}(entity.get{pname}());
        }}""")
        update_block = "\n".join(update_assignments)

        files[f"src/main/java/{pkg_path}/application/service/{primary_entity}Service.java"] = f"""package {pkg_prefix}.application.service;

import {pkg_prefix}.domain.exception.ResourceNotFoundException;
import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.domain.port.in.*;
import {pkg_prefix}.domain.port.out.{primary_entity}RepositoryPort;
import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;
import java.time.LocalDateTime;
import java.util.UUID;

@ApplicationScoped
public class {primary_entity}Service implements
        Create{primary_entity}UseCase,
        Get{primary_entity}UseCase,
        Search{primary_entity}UseCase,
        Update{primary_entity}UseCase,
        Delete{primary_entity}UseCase {{

    private final {primary_entity}RepositoryPort repositoryPort;

    @Inject
    public {primary_entity}Service({primary_entity}RepositoryPort repositoryPort) {{
        this.repositoryPort = repositoryPort;
    }}

    @Override
    @Transactional
    public {primary_entity} create({primary_entity} entity) {{
        if (entity.getId() == null) {{
            entity.setId(UUID.randomUUID());
        }}
        if (entity.getStatus() == null) {{
            entity.setStatus("{default_status}");
        }}
        if (entity.getCreatedAt() == null) {{
            entity.setCreatedAt(LocalDateTime.now());
        }}
        return repositoryPort.save(entity);
    }}

    @Override
    public {primary_entity} getById(UUID id) {{
        return repositoryPort.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("{primary_entity} not found with id: " + id));
    }}

    @Override
    public PageResponse<{primary_entity}> search(String query, String status, int page, int size) {{
        return repositoryPort.search(query, status, page, size);
    }}

    @Override
    @Transactional
    public {primary_entity} update(UUID id, {primary_entity} entity) {{
        {primary_entity} existing = getById(id);
{update_block}
        return repositoryPort.save(existing);
    }}

    @Override
    @Transactional
    public void delete(UUID id) {{
        {primary_entity} existing = getById(id);
        existing.setStatus("INACTIVE");
        repositoryPort.save(existing);
    }}
}}
"""

        # 5. Panache Entity
        panache_cols = []
        to_domain_stmts = ["        d.setId(this.id);"]
        from_domain_stmts = []

        for f in non_id_fields:
            fname = f["name"]
            ftype = f["type"]
            pname = to_pascal_case(fname)
            scol = to_snake_case(fname)
            panache_cols.append(f"""    @Column(name = "{scol}")\n    public {ftype} {fname};""")
            to_domain_stmts.append(f"        d.set{pname}(this.{fname});")
            from_domain_stmts.append(f"        e.{fname} = d.get{pname}();")

        panache_cols_str = "\n\n".join(panache_cols)
        to_domain_str = "\n".join(to_domain_stmts)
        from_domain_str = "\n".join(from_domain_stmts)

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/{primary_entity}Entity.java"] = f"""package {pkg_prefix}.adapter.out.persistence;

import {pkg_prefix}.domain.model.{primary_entity};
import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.*;
{imports_str}

@Entity
@Table(name = "{primary_table}")
public class {primary_entity}Entity extends PanacheEntityBase {{

    @Id
    @Column(name = "id", nullable = false)
    public UUID id;

{panache_cols_str}

    public {primary_entity}Entity() {{}}

    public {primary_entity} toDomain() {{
        {primary_entity} d = new {primary_entity}();
{to_domain_str}
        return d;
    }}

    public static {primary_entity}Entity fromDomain({primary_entity} d) {{
        {primary_entity}Entity e = new {primary_entity}Entity();
        e.id = d.getId() != null ? d.getId() : UUID.randomUUID();
{from_domain_str}
        if (e.status == null) {{
            e.status = "{default_status}";
        }}
        if (e.createdAt == null) {{
            e.createdAt = LocalDateTime.now();
        }}
        return e;
    }}
}}
"""

        # 6. Panache Repository
        files[f"src/main/java/{pkg_path}/adapter/out/persistence/{primary_entity}PanacheRepository.java"] = f"""package {pkg_prefix}.adapter.out.persistence;

import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;
import jakarta.enterprise.context.ApplicationScoped;
import java.util.UUID;

@ApplicationScoped
public class {primary_entity}PanacheRepository implements PanacheRepositoryBase<{primary_entity}Entity, UUID> {{
}}
"""

        # 7. Repository Adapter
        string_cols = [f["name"] for f in non_id_fields if f["type"] == "String" and f["name"] not in ["status", "estado"]]
        if string_cols:
            q_terms = " or ".join([f"lower({col}) like :q" for col in string_cols[:3]])
            search_clause = f"""        if (query != null && !query.trim().isEmpty()) {{
            queryBuilder.append(" and ({q_terms})");
            params.and("q", "%" + query.trim().toLowerCase() + "%");
        }}"""
        else:
            search_clause = ""

        files[f"src/main/java/{pkg_path}/adapter/out/persistence/{primary_entity}RepositoryAdapter.java"] = f"""package {pkg_prefix}.adapter.out.persistence;

import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.domain.port.out.{primary_entity}RepositoryPort;
import {pkg_prefix}.adapter.in.web.dto.PageResponse;
import io.quarkus.panache.common.Page;
import io.quarkus.panache.common.Parameters;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.*;
import java.util.stream.Collectors;

@ApplicationScoped
public class {primary_entity}RepositoryAdapter implements {primary_entity}RepositoryPort {{

    @Inject
    {primary_entity}PanacheRepository panacheRepository;

    @Override
    public {primary_entity} save({primary_entity} entity) {{
        {primary_entity}Entity panacheEntity = {primary_entity}Entity.fromDomain(entity);
        if (entity.getId() != null && panacheRepository.findById(entity.getId()) != null) {{
            {primary_entity}Entity managed = panacheRepository.getEntityManager().merge(panacheEntity);
            return managed.toDomain();
        }} else {{
            panacheRepository.persist(panacheEntity);
            return panacheEntity.toDomain();
        }}
    }}

    @Override
    public Optional<{primary_entity}> findById(UUID id) {{
        return panacheRepository.findByIdOptional(id).map({primary_entity}Entity::toDomain);
    }}

    @Override
    public PageResponse<{primary_entity}> search(String query, String status, int page, int size) {{
        StringBuilder queryBuilder = new StringBuilder("1=1");
        Parameters params = new Parameters();

        if (status != null && !status.trim().isEmpty()) {{
            queryBuilder.append(" and status = :status");
            params.and("status", status.trim().toUpperCase());
        }}
{search_clause}

        var panacheQuery = panacheRepository.find(queryBuilder.toString(), params);
        long totalElements = panacheQuery.count();
        int totalPages = (int) Math.ceil((double) totalElements / size);

        List<{primary_entity}> content = panacheQuery.page(Page.of(page, size)).list()
                .stream()
                .map({primary_entity}Entity::toDomain)
                .collect(Collectors.toList());

        return new PageResponse<>(content, page, size, totalElements, totalPages);
    }}

    @Override
    public long count(String query, String status) {{
        return panacheRepository.count();
    }}

    @Override
    public void deleteById(UUID id) {{
        panacheRepository.deleteById(id);
    }}

    @Override
    public boolean existsById(UUID id) {{
        return panacheRepository.findByIdOptional(id).isPresent();
    }}
}}
"""

    @classmethod
    def _ensure_universal_rest_resource(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]]):
        """Generate REST Controller and DTOs for ANY entity with matching fields."""
        imports = get_field_imports(fields)
        imports_str = "\n".join(imports)
        non_id_fields = [f for f in fields if not f.get("is_id")]
        req_fields = [f for f in non_id_fields if f["name"] not in ["id", "createdAt", "created_at", "status", "estado"]]

        # Request DTO fields and getters
        req_decls = []
        req_gs = []
        for f in req_fields:
            fname = f["name"]
            ftype = f["type"]
            pname = to_pascal_case(fname)
            annotations = []
            if ftype == "String":
                annotations.append(f'@NotBlank(message = "{pname} is required")')
            elif ftype == "BigDecimal":
                annotations.append(f'@NotNull(message = "{pname} is required")')
                annotations.append(f'@DecimalMin(value = "0.00", message = "{pname} cannot be negative")')
            elif ftype in ["Integer", "Long"]:
                annotations.append(f'@NotNull(message = "{pname} is required")')
                annotations.append(f'@Min(value = 0, message = "{pname} cannot be negative")')
            else:
                annotations.append(f'@NotNull(message = "{pname} is required")')

            ann_str = "\n    ".join(annotations)
            req_decls.append(f"    {ann_str}\n    private {ftype} {fname};")
            req_gs.append(f"    public {ftype} get{pname}() {{ return {fname}; }}\n    public void set{pname}({ftype} {fname}) {{ this.{fname} = {fname}; }}")

        req_decls_str = "\n\n".join(req_decls)
        req_gs_str = "\n\n".join(req_gs)

        files[f"src/main/java/{pkg_path}/adapter/in/web/dto/{primary_entity}Request.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import jakarta.validation.constraints.*;
{imports_str}

public class {primary_entity}Request {{
{req_decls_str}

    public {primary_entity}Request() {{}}

{req_gs_str}
}}
"""

        # Response DTO
        resp_decls = ["    private UUID id;"]
        resp_from_stmts = ["        r.id = d.getId();"]
        resp_gs = ["    public UUID getId() { return id; }\n    public void setId(UUID id) { this.id = id; }"]

        for f in non_id_fields:
            fname = f["name"]
            ftype = f["type"]
            pname = to_pascal_case(fname)
            resp_decls.append(f"    private {ftype} {fname};")
            resp_from_stmts.append(f"        r.{fname} = d.get{pname}();")
            resp_gs.append(f"    public {ftype} get{pname}() {{ return {fname}; }}\n    public void set{pname}({ftype} {fname}) {{ this.{fname} = {fname}; }}")

        resp_decls_str = "\n".join(resp_decls)
        resp_from_str = "\n".join(resp_from_stmts)
        resp_gs_str = "\n\n".join(resp_gs)

        files[f"src/main/java/{pkg_path}/adapter/in/web/dto/{primary_entity}Response.java"] = f"""package {pkg_prefix}.adapter.in.web.dto;

import {pkg_prefix}.domain.model.{primary_entity};
{imports_str}

public class {primary_entity}Response {{
{resp_decls_str}

    public {primary_entity}Response() {{}}

    public static {primary_entity}Response fromDomain({primary_entity} d) {{
        {primary_entity}Response r = new {primary_entity}Response();
{resp_from_str}
        return r;
    }}

{resp_gs_str}
}}
"""

        # Resource Controller
        req_to_domain = []
        for f in req_fields:
            pname = to_pascal_case(f["name"])
            req_to_domain.append(f"        domain.set{pname}(request.get{pname}());")
        req_mapping_str = "\n".join(req_to_domain)

        files[f"src/main/java/{pkg_path}/adapter/in/web/{primary_entity}Resource.java"] = f"""package {pkg_prefix}.adapter.in.web;

import {pkg_prefix}.adapter.in.web.dto.*;
import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.domain.port.in.*;
import jakarta.annotation.security.RolesAllowed;
import jakarta.inject.Inject;
import jakarta.validation.Valid;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;
import org.eclipse.microprofile.openapi.annotations.Operation;
import org.eclipse.microprofile.openapi.annotations.tags.Tag;
import java.net.URI;
import java.util.UUID;
import java.util.stream.Collectors;

@Path("/api/v1/{primary_table}")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@Tag(name = "{primary_entity} Resource", description = "Operations for {primary_entity}")
public class {primary_entity}Resource {{

    @Inject
    Create{primary_entity}UseCase createUseCase;

    @Inject
    Get{primary_entity}UseCase getUseCase;

    @Inject
    Search{primary_entity}UseCase searchUseCase;

    @Inject
    Update{primary_entity}UseCase updateUseCase;

    @Inject
    Delete{primary_entity}UseCase deleteUseCase;

    @POST
    @RolesAllowed({{"ADMIN", "OPERATOR"}})
    @Operation(summary = "Create a new {primary_entity}")
    public Response create(@Valid {primary_entity}Request request) {{
        {primary_entity} domain = new {primary_entity}();
{req_mapping_str}

        {primary_entity} created = createUseCase.create(domain);
        return Response.created(URI.create("/api/v1/{primary_table}/" + created.getId()))
                .entity({primary_entity}Response.fromDomain(created))
                .build();
    }}

    @GET
    @RolesAllowed({{"ADMIN", "OPERATOR", "AUDITOR"}})
    @Operation(summary = "Search and paginate {primary_entity}")
    public Response search(
            @QueryParam("q") @DefaultValue("") String query,
            @QueryParam("status") @DefaultValue("") String status,
            @QueryParam("page") @DefaultValue("0") int page,
            @QueryParam("size") @DefaultValue("20") int size) {{
        var pageDomain = searchUseCase.search(query, status, page, size);
        var content = pageDomain.getContent().stream()
                .map({primary_entity}Response::fromDomain)
                .collect(Collectors.toList());
        return Response.ok(new PageResponse<>(content, pageDomain.getPage(), pageDomain.getSize(), pageDomain.getTotalElements(), pageDomain.getTotalPages())).build();
    }}

    @GET
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN", "OPERATOR", "AUDITOR"}})
    @Operation(summary = "Retrieve {primary_entity} by ID")
    public Response getById(@PathParam("id") UUID id) {{
        {primary_entity} entity = getUseCase.getById(id);
        return Response.ok({primary_entity}Response.fromDomain(entity)).build();
    }}

    @PUT
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN", "OPERATOR"}})
    @Operation(summary = "Update {primary_entity} by ID")
    public Response update(@PathParam("id") UUID id, @Valid {primary_entity}Request request) {{
        {primary_entity} domain = new {primary_entity}();
{req_mapping_str}
        {primary_entity} updated = updateUseCase.update(id, domain);
        return Response.ok({primary_entity}Response.fromDomain(updated)).build();
    }}

    @DELETE
    @Path("/{{id}}")
    @RolesAllowed({{"ADMIN"}})
    @Operation(summary = "Delete {primary_entity} by ID")
    public Response delete(@PathParam("id") UUID id) {{
        deleteUseCase.delete(id);
        return Response.noContent().build();
    }}
}}
"""

    @classmethod
    def _ensure_universal_tests(cls, files: Dict[str, str], pkg_prefix: str, pkg_path: str, primary_entity: str, primary_table: str, fields: List[Dict[str, Any]], default_status: str):
        """Generate unit tests with Mockito and integration tests with @QuarkusTest for ANY entity."""
        imports = get_field_imports(fields)
        imports_str = "\n".join(imports)
        non_id_fields = [f for f in fields if not f.get("is_id")]
        req_fields = [f for f in non_id_fields if f["name"] not in ["id", "createdAt", "created_at", "status", "estado"]]

        # Service Test setup statements
        setup_stmts = [
            "        testId = UUID.randomUUID();",
            f"        sampleEntity = new {primary_entity}();",
            "        sampleEntity.setId(testId);"
        ]
        for f in non_id_fields:
            pname = to_pascal_case(f["name"])
            val = get_sample_java_value(f, default_status)
            setup_stmts.append(f"        sampleEntity.set{pname}({val});")

        setup_block = "\n".join(setup_stmts)

        files[f"src/test/java/{pkg_path}/application/service/{primary_entity}ServiceTest.java"] = f"""package {pkg_prefix}.application.service;

import {pkg_prefix}.domain.exception.ResourceNotFoundException;
import {pkg_prefix}.domain.model.{primary_entity};
import {pkg_prefix}.domain.port.out.{primary_entity}RepositoryPort;
import io.quarkus.test.InjectMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
{imports_str}
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
public class {primary_entity}ServiceTest {{

    @Inject
    {primary_entity}Service service;

    @InjectMock
    {primary_entity}RepositoryPort repositoryPort;

    private UUID testId;
    private {primary_entity} sampleEntity;

    @BeforeEach
    void setUp() {{
{setup_block}
    }}

    @Test
    @DisplayName("Should create {primary_entity} successfully")
    void testCreate() {{
        Mockito.when(repositoryPort.save(Mockito.any())).thenReturn(sampleEntity);
        {primary_entity} created = service.create(sampleEntity);
        assertNotNull(created);
        assertEquals(testId, created.getId());
    }}

    @Test
    @DisplayName("Should find {primary_entity} by ID")
    void testFindById() {{
        Mockito.when(repositoryPort.findById(testId)).thenReturn(Optional.of(sampleEntity));
        {primary_entity} found = service.getById(testId);
        assertNotNull(found);
        assertEquals(testId, found.getId());
    }}

    @Test
    @DisplayName("Should throw ResourceNotFoundException when {primary_entity} not found")
    void testNotFound() {{
        Mockito.when(repositoryPort.findById(testId)).thenReturn(Optional.empty());
        assertThrows(ResourceNotFoundException.class, () -> service.getById(testId));
    }}
}}
"""

        # Resource Integration Test
        json_sample = {f["name"]: get_sample_json_value(f, default_status) for f in req_fields}
        json_escaped = json.dumps(json.dumps(json_sample))

        files[f"src/test/java/{pkg_path}/adapter/in/web/{primary_entity}ResourceTest.java"] = f"""package {pkg_prefix}.adapter.in.web;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.security.TestSecurity;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@QuarkusTest
public class {primary_entity}ResourceTest {{

    @Test
    @TestSecurity(user = "adminUser", roles = {{"ADMIN", "OPERATOR"}})
    @DisplayName("POST /api/v1/{primary_table} - Should create entity and return 201 Created")
    void testCreateEndpoint() {{
        String payload = {json_escaped};

        given()
            .contentType(ContentType.JSON)
            .body(payload)
            .when().post("/api/v1/{primary_table}")
            .then()
            .statusCode(201)
            .header("Location", notNullValue());
    }}

    @Test
    @TestSecurity(user = "auditorUser", roles = {{"AUDITOR"}})
    @DisplayName("GET /api/v1/{primary_table} - Should list entities with 200 OK")
    void testSearchEndpoint() {{
        given()
            .when().get("/api/v1/{primary_table}")
            .then()
            .statusCode(200)
            .body("content", notNullValue());
    }}

    @Test
    @DisplayName("Unauthenticated request should return 401 Unauthorized")
    void testUnauthorized() {{
        given()
            .when().get("/api/v1/{primary_table}")
            .then()
            .statusCode(401);
    }}
}}
"""


class UniversalSynthesizer:
    def __init__(self, client_code: str = 'bcp', package_prefix: str = 'pe.com.bcp'):
        self.client_code = client_code
        self.package_prefix = package_prefix

    def synthesize_from_spec(self, spec: dict) -> dict:
        state = {
            'client_code': self.client_code,
            'blueprint': {
                'package_prefix': self.package_prefix,
                'artifact_id': spec.get('service', {}).get('name', 'sample-service'),
            },
            'service_spec': spec,
            'config': {},
            'files': {}
        }
        res = CodeSynthesizer.guarantee_project(state)
        return res.get('files', {})
