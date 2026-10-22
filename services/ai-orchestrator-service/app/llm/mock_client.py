import json
import re
import uuid
from typing import Any, Dict, List, Tuple
from app.llm.base import BaseLLMClient


def _extract_blueprint_from_prompt(user_prompt: str) -> dict:
    if "Blueprint:" not in user_prompt:
        return {}
    part = user_prompt.split("Blueprint:", 1)[1]
    for stopper in ["\nExisting Files:", "\nGovernance:", "\nUser "]:
        if stopper in part:
            part = part.split(stopper, 1)[0]
    part = part.strip()
    try:
        return json.loads(part)
    except Exception:
        start = part.find("{")
        if start != -1:
            depth = 0
            for i, ch in enumerate(part[start:], start=start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(part[start:i+1])
                        except Exception:
                            pass
                        break
    return {}


class MockLLMClient(BaseLLMClient):
    """Enterprise offline Quarkus Microservice Generator producing complete, compilable solutions."""

    def __init__(self, mode: str = "balanced"):
        self.mode = mode

    def test_connection(self) -> bool:
        return True

    def _extract_param(self, text: str, prefix: str, default: str = "") -> str:
        for line in text.splitlines():
            if line.strip().startswith(prefix):
                return line.split(prefix, 1)[1].strip()
        return default

    def _extract_json_field(self, text: str, field_name: str) -> Any:
        pattern = rf"{field_name}:\s*(\[.*?\]|\{{.*?\}})"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> Tuple[str, int, int]:
        prompt_tokens = len(system_prompt.split()) + len(user_prompt.split())

        # Extract parameters from user_prompt
        client_code = self._extract_param(user_prompt, "Client Code:", "bcp").lower()
        default_pkg = f"pe.com.{client_code}"
        
        user_pkg = self._extract_param(user_prompt, "User Package Prefix:", "")
        package_prefix = user_pkg if (user_pkg and user_pkg != "None") else default_pkg

        raw_arch = self._extract_param(user_prompt, "User Architecture Selection:", "Hexagonal")
        if "hex" in raw_arch.lower():
            arch_style = "Hexagonal"
        elif "layer" in raw_arch.lower():
            arch_style = "Layered"
        elif "clean" in raw_arch.lower():
            arch_style = "Clean"
        elif "event" in raw_arch.lower():
            arch_style = "Event-Driven"
        else:
            arch_style = raw_arch.capitalize()

        security_opt = self._extract_param(user_prompt, "User Security Selection:", "JWT").upper()
        db_opt = self._extract_param(user_prompt, "User Database Selection:", "POSTGRESQL_PANACHE").upper()
        artifact_id = self._extract_param(user_prompt, "User Artifact ID:", f"{client_code}-service")
        if not artifact_id or artifact_id == "None":
            artifact_id = f"{client_code}-service"

        http_port = self._extract_param(user_prompt, "User HTTP Port:", "8080")
        if not http_port or http_port == "None":
            http_port = "8080"

        java_version = self._extract_param(user_prompt, "User Java Version:", "21")
        if not java_version or java_version == "None":
            java_version = "21"

        quarkus_version = self._extract_param(user_prompt, "User Quarkus Version:", "3.15.1")
        if not quarkus_version or quarkus_version == "None":
            quarkus_version = "3.15.1"

        build_tool = self._extract_param(user_prompt, "User Build Tool:", "maven").lower()
        if "gradle" in build_tool:
            build_tool = "gradle"
        else:
            build_tool = "maven"

        database_name = self._extract_param(user_prompt, "User Database Name:", f"{client_code}_db")
        if not database_name or database_name == "None":
            database_name = f"{client_code}_db"

        custom_endpoints = self._extract_json_field(user_prompt, "User Custom Endpoints")
        custom_extensions = self._extract_json_field(user_prompt, "User Custom Free Extensions")
        custom_properties = self._extract_json_field(user_prompt, "User Custom Properties")
        user_entities = self._extract_json_field(user_prompt, "User Defined Entities") or self._extract_json_field(user_prompt, "Configured Entities")
        design_patterns = self._extract_json_field(user_prompt, "User Design Patterns") or ["REPOSITORY", "BUILDER"]

        # Parse requirements to infer domain if entities are empty
        req_text = self._extract_param(user_prompt, "Requirements:", "").lower()
        art_id = artifact_id.lower()

        if not user_entities or not isinstance(user_entities, list) or len(user_entities) == 0:
            # Semantic inference from requirement
            if any(k in req_text or k in art_id for k in ["fraude", "fraud", "reclamo", "disputa"]):
                entity_name = "FraudClaim"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "customerDni", "type": "String", "required": True},
                    {"name": "maskedCard", "type": "String", "required": True},
                    {"name": "fraudAmount", "type": "BigDecimal", "required": True},
                    {"name": "reason", "type": "String", "required": True},
                    {"name": "observations", "type": "String", "required": False},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            elif any(k in req_text or k in art_id for k in ["poliza", "seguro", "insurance", "policy"]):
                entity_name = "Policy"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "policyNumber", "type": "String", "required": True},
                    {"name": "holderDni", "type": "String", "required": True},
                    {"name": "premiumAmount", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "startDate", "type": "LocalDateTime", "required": True},
                ]
            elif any(k in req_text or k in art_id for k in ["prestamo", "loan", "credito"]):
                entity_name = "Loan"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "applicantDni", "type": "String", "required": True},
                    {"name": "amount", "type": "BigDecimal", "required": True},
                    {"name": "interestRate", "type": "BigDecimal", "required": True},
                    {"name": "termMonths", "type": "Integer", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            elif any(k in req_text or k in art_id for k in ["tarjeta", "card"]):
                entity_name = "CreditCard"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "cardNumberMasked", "type": "String", "required": True},
                    {"name": "holderName", "type": "String", "required": True},
                    {"name": "creditLimit", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "expiryDate", "type": "String", "required": True},
                ]
            elif any(k in req_text or k in art_id for k in ["pago", "payment", "transfer"]):
                entity_name = "Payment"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "sourceAccount", "type": "String", "required": True},
                    {"name": "destinationAccount", "type": "String", "required": True},
                    {"name": "amount", "type": "BigDecimal", "required": True},
                    {"name": "currency", "type": "String", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "timestamp", "type": "LocalDateTime", "required": True},
                ]
            else:
                entity_name = "Account"
                fields = [
                    {"name": "id", "type": "UUID", "required": True, "isId": True},
                    {"name": "accountNumber", "type": "String", "required": True},
                    {"name": "balance", "type": "BigDecimal", "required": True},
                    {"name": "currency", "type": "String", "required": True},
                    {"name": "status", "type": "String", "required": True},
                    {"name": "createdAt", "type": "LocalDateTime", "required": True},
                ]
            entities = [{"name": entity_name, "tableName": f"{entity_name.lower()}s", "fields": fields}]
        else:
            entities = user_entities

        # -------------------------------------------------------------
        # Node 0: ServiceSpec Builder Prompt
        # -------------------------------------------------------------
        if any(k in system_prompt for k in ["ServiceSpec", "Principal Software Architect", "spec_builder"]):
            ent0 = entities[0] if entities else {"name": "Item", "tableName": "items", "fields": []}
            spec_dict = {
                "service": {
                    "name": artifact_id,
                    "purpose": req_text or "Enterprise Quarkus microservice with hexagonal architecture",
                    "archetype_hint": "hexagonal"
                },
                "inbound": [
                    {
                        "id": "rest-inbound-primary",
                        "kind": "rest",
                        "details": {
                            "path": f"/api/v1/{ent0.get('tableName', 'items')}",
                            "methods": ["GET", "POST", "PUT", "DELETE"],
                            "summary": f"Operations for {ent0.get('name', 'Item')}"
                        }
                    }
                ],
                "outbound": [
                    {
                        "id": "db-outbound-primary",
                        "kind": "database",
                        "details": {
                            "db_type": db_opt,
                            "type": db_opt
                        }
                    }
                ],
                "domain": {
                    "data_models": [
                        {
                            "name": ent0.get("name", "Item"),
                            "table_name": ent0.get("tableName", f"{ent0.get('name', 'item').lower()}s"),
                            "fields": ent0.get("fields", [])
                        }
                    ]
                },
                "behaviors": [
                    {
                        "id": "behavior-crud-create",
                        "given": "System is running and connected",
                        "when": f"POST request to /api/v1/{ent0.get('tableName', 'items')} with valid payload",
                        "then": "Entity is persisted and 201 Created is returned"
                    }
                ],
                "non_functional": {
                    "security": {"auth_type": security_opt, "roles": ["ADMIN", "OPERATOR"]},
                    "resilience": {"timeout_ms": 3000, "circuit_breaker": True}
                }
            }
            spec_json = json.dumps(spec_dict, indent=2)
            return spec_json, prompt_tokens, len(spec_json.split())

        # -------------------------------------------------------------
        # Node 1: Blueprint design prompt
        # -------------------------------------------------------------
        if "BLUEPRINT_DESIGN_NODE" in system_prompt:
            dependencies = [
                "quarkus-resteasy-reactive-jackson",
                "quarkus-smallrye-openapi",
                "quarkus-hibernate-validator",
                "quarkus-smallrye-health",
                "quarkus-micrometer-registry-prometheus",
            ]
            if "JWT" in security_opt:
                dependencies.append("quarkus-smallrye-jwt")
            elif "OIDC" in security_opt:
                dependencies.append("quarkus-oidc")

            is_stateless = ("NONE" in db_opt or db_opt == "NONE")
            if not is_stateless:
                if "SQLSERVER" in db_opt:
                    dependencies.extend(["quarkus-hibernate-orm-panache", "quarkus-jdbc-mssql"])
                elif "POSTGRESQL" in db_opt:
                    dependencies.extend(["quarkus-hibernate-orm-panache", "quarkus-jdbc-postgresql"])
                elif "MONGODB" in db_opt:
                    dependencies.append("quarkus-mongodb-panache")

            # Check kafka / events
            if "OUTBOX" in str(design_patterns) or "kafka" in user_prompt.lower() or "event" in user_prompt.lower():
                dependencies.append("quarkus-smallrye-reactive-messaging-kafka")

            if custom_extensions and isinstance(custom_extensions, list):
                for ext in custom_extensions:
                    if ext and ext not in dependencies:
                        dependencies.append(ext.strip())

            endpoints_list = []
            if custom_endpoints and isinstance(custom_endpoints, list) and len(custom_endpoints) > 0:
                for ep in custom_endpoints:
                    endpoints_list.append({
                        "path": ep.get("path"),
                        "method": ep.get("method", "GET"),
                        "summary": ep.get("summary", "Operación REST"),
                    })
            else:
                for ent in entities:
                    e_name = ent.get("name", "Item").lower()
                    endpoints_list.extend([
                        {"path": f"/api/v1/{e_name}s", "method": "POST", "summary": f"Registrar nuevo {ent.get('name')}"},
                        {"path": f"/api/v1/{e_name}s/{{id}}", "method": "GET", "summary": f"Consultar {ent.get('name')} por UUID"},
                        {"path": f"/api/v1/{e_name}s", "method": "GET", "summary": f"Listar {ent.get('name')}s activos"},
                    ])

            output = {
                "architecture_style": arch_style,
                "artifact_id": artifact_id,
                "build_tool": build_tool,
                "quarkus_version": quarkus_version,
                "java_version": java_version,
                "package_prefix": package_prefix,
                "dependencies": dependencies,
                "entities": entities,
                "endpoints": endpoints_list,
                "design_patterns": design_patterns,
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 2: Scaffolding generation prompt
        # -------------------------------------------------------------
        if "SCAFFOLDING_NODE" in system_prompt:
            bp = _extract_blueprint_from_prompt(user_prompt)

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_java = bp.get("java_version", java_version)
            effective_artifact = bp.get("artifact_id", artifact_id)
            effective_build_tool = bp.get("build_tool", build_tool)
            is_stateless = ("NONE" in db_opt or db_opt == "NONE")

            # Properties content
            props_content = (
                f'# ===================================================================\n'
                f'# TCS Intelligent Microservice Factory -- {effective_artifact}\n'
                f'# Cliente: {client_code.upper()} | Stack: Java {effective_java} + Quarkus {quarkus_version}\n'
                f'# ===================================================================\n\n'
                f'quarkus.http.port={http_port}\n'
                f'quarkus.application.name={effective_artifact}\n'
                f'quarkus.http.cors=true\n\n'
                f'# Observabilidad & OpenAPI (SmallRye)\n'
                f'quarkus.smallrye-openapi.path=/q/openapi\n'
                f'quarkus.swagger-ui.always-include=true\n'
                f'quarkus.smallrye-health.root-path=/q/health\n'
                f'quarkus.micrometer.export.prometheus.path=/q/metrics\n'
            )

            if not is_stateless:
                if "SQLSERVER" in db_opt:
                    props_content += (
                        '\n# Database Configuration (Microsoft SQL Server BCP)\n'
                        'quarkus.datasource.db-kind=mssql\n'
                        f'quarkus.datasource.jdbc.url=jdbc:sqlserver://${{DB_HOST:localhost}}:${{DB_PORT:1433}};databaseName=${{DB_NAME:{database_name}}};encrypt=true;trustServerCertificate=true;\n'
                        'quarkus.datasource.username=${DB_USER:sa}\n'
                        'quarkus.datasource.password=${DB_PASSWORD:SecretPass123!}\n'
                        'quarkus.hibernate-orm.database.generation=update\n'
                        'quarkus.hibernate-orm.log.sql=false\n'
                    )
                elif "POSTGRESQL" in db_opt:
                    props_content += (
                        '\n# Database Configuration (PostgreSQL Panache)\n'
                        'quarkus.datasource.db-kind=postgresql\n'
                        f'quarkus.datasource.jdbc.url=jdbc:postgresql://${{DB_HOST:localhost}}:${{DB_PORT:5432}}/${{DB_NAME:{database_name}}}\n'
                        'quarkus.datasource.username=${DB_USER:postgres}\n'
                        'quarkus.datasource.password=${DB_PASSWORD:postgres}\n'
                        'quarkus.hibernate-orm.database.generation=update\n'
                        'quarkus.hibernate-orm.log.sql=false\n'
                    )

            if "JWT" in security_opt:
                props_content += (
                    '\n# Security (SmallRye JWT BCP)\n'
                    f'mp.jwt.verify.issuer=${{JWT_ISSUER:https://auth.via{client_code}.com}}\n'
                    'mp.jwt.verify.publickey.location=META-INF/resources/publicKey.pem\n'
                )

            # Kafka channels if enabled
            if "OUTBOX" in str(design_patterns) or "kafka" in user_prompt.lower():
                props_content += (
                    '\n# Apache Kafka Reactive Messaging Channels\n'
                    f'mp.messaging.outgoing.{client_code}-events-out.connector=smallrye-kafka\n'
                    f'mp.messaging.outgoing.{client_code}-events-out.topic=pe.com.{client_code}.events.v1\n'
                    f'mp.messaging.outgoing.{client_code}-events-out.value.serializer=org.apache.kafka.common.serialization.StringSerializer\n'
                    'kafka.bootstrap.servers=${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}\n'
                )

            if custom_properties:
                props_content += "\n# Propiedades Personalizadas de Usuario\n"
                if isinstance(custom_properties, dict):
                    for k, v in custom_properties.items():
                        props_content += f"{k}={v}\n"
                elif isinstance(custom_properties, str):
                    props_content += f"{custom_properties.strip()}\n"

            files_map = {
                "src/main/resources/application.properties": props_content,
                ".github/workflows/ci.yml": (
                    'name: Quarkus Microservice CI/CD\n'
                    'on: [push, pull_request]\n'
                    'jobs:\n'
                    '  build:\n'
                    '    runs-on: ubuntu-latest\n'
                    '    steps:\n'
                    '      - uses: actions/checkout@v4\n'
                    '      - uses: actions/setup-java@v4\n'
                    '        with:\n'
                    f'          java-version: "{effective_java}"\n'
                    '          distribution: "temurin"\n'
                    f'      - run: {"./gradlew check" if effective_build_tool == "gradle" else "mvn -B clean test"}\n'
                ),
            }

            if effective_build_tool == "gradle":
                # Generate build.gradle & settings.gradle
                settings_gradle = f'rootProject.name = "{effective_artifact}"\n'
                build_gradle = (
                    'plugins {\n'
                    '    id "java"\n'
                    '    id "io.quarkus" version "3.15.1"\n'
                    '}\n\n'
                    'repositories {\n'
                    '    mavenCentral()\n'
                    '}\n\n'
                    'dependencies {\n'
                    '    implementation enforcedPlatform("io.quarkus.platform:quarkus-bom:3.15.1")\n'
                    '    implementation "io.quarkus:quarkus-resteasy-reactive-jackson"\n'
                    '    implementation "io.quarkus:quarkus-smallrye-openapi"\n'
                    '    implementation "io.quarkus:quarkus-hibernate-validator"\n'
                    '    implementation "io.quarkus:quarkus-smallrye-health"\n'
                    '    implementation "io.quarkus:quarkus-micrometer-registry-prometheus"\n'
                )
                if "JWT" in security_opt:
                    build_gradle += '    implementation "io.quarkus:quarkus-smallrye-jwt"\n'
                if not is_stateless:
                    if "SQLSERVER" in db_opt:
                        build_gradle += '    implementation "io.quarkus:quarkus-hibernate-orm-panache"\n'
                        build_gradle += '    implementation "io.quarkus:quarkus-jdbc-mssql"\n'
                    elif "POSTGRESQL" in db_opt:
                        build_gradle += '    implementation "io.quarkus:quarkus-hibernate-orm-panache"\n'
                        build_gradle += '    implementation "io.quarkus:quarkus-jdbc-postgresql"\n'
                if "OUTBOX" in str(design_patterns):
                    build_gradle += '    implementation "io.quarkus:quarkus-smallrye-reactive-messaging-kafka"\n'
                build_gradle += (
                    '    testImplementation "io.quarkus:quarkus-junit5"\n'
                    '    testImplementation "io.rest-assured:rest-assured"\n'
                    '}\n\n'
                    f'group = "{effective_pkg}"\n'
                    'version = "1.0.0-SNAPSHOT"\n\n'
                    f'java {{\n    sourceCompatibility = JavaVersion.VERSION_{effective_java}\n    targetCompatibility = JavaVersion.VERSION_{effective_java}\n}}\n'
                )
                files_map["build.gradle"] = build_gradle
                files_map["settings.gradle"] = settings_gradle
            else:
                # Generate pom.xml
                pom_content = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<project xmlns="http://maven.apache.org/POM/4.0.0"\n'
                    '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                    '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">\n'
                    '  <modelVersion>4.0.0</modelVersion>\n'
                    f'  <groupId>{effective_pkg}</groupId>\n'
                    f'  <artifactId>{effective_artifact}</artifactId>\n'
                    '  <version>1.0.0-SNAPSHOT</version>\n\n'
                    '  <properties>\n'
                    f'    <maven.compiler.release>{effective_java}</maven.compiler.release>\n'
                    '    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>\n'
                    '    <quarkus.platform.artifact-id>quarkus-bom</quarkus.platform.artifact-id>\n'
                    '    <quarkus.platform.group-id>io.quarkus.platform</quarkus.platform.group-id>\n'
                    f'    <quarkus.platform.version>{quarkus_version}</quarkus.platform.version>\n'
                    '  </properties>\n\n'
                    '  <dependencyManagement>\n'
                    '    <dependencies>\n'
                    '      <dependency>\n'
                    '        <groupId>${quarkus.platform.group-id}</groupId>\n'
                    '        <artifactId>${quarkus.platform.artifact-id}</artifactId>\n'
                    '        <version>${quarkus.platform.version}</version>\n'
                    '        <type>pom</type>\n'
                    '        <scope>import</scope>\n'
                    '      </dependency>\n'
                    '    </dependencies>\n'
                    '  </dependencyManagement>\n\n'
                    '  <dependencies>\n'
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-resteasy-reactive-jackson</artifactId>\n'
                    '    </dependency>\n'
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-smallrye-openapi</artifactId>\n'
                    '    </dependency>\n'
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-hibernate-validator</artifactId>\n'
                    '    </dependency>\n'
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-smallrye-health</artifactId>\n'
                    '    </dependency>\n'
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-micrometer-registry-prometheus</artifactId>\n'
                    '    </dependency>\n'
                )
                if "JWT" in security_opt:
                    pom_content += (
                        '    <dependency>\n'
                        '      <groupId>io.quarkus</groupId>\n'
                        '      <artifactId>quarkus-smallrye-jwt</artifactId>\n'
                        '    </dependency>\n'
                    )
                if not is_stateless:
                    if "SQLSERVER" in db_opt:
                        pom_content += (
                            '    <dependency>\n'
                            '      <groupId>io.quarkus</groupId>\n'
                            '      <artifactId>quarkus-hibernate-orm-panache</artifactId>\n'
                            '    </dependency>\n'
                            '    <dependency>\n'
                            '      <groupId>io.quarkus</groupId>\n'
                            '      <artifactId>quarkus-jdbc-mssql</artifactId>\n'
                            '    </dependency>\n'
                        )
                    elif "POSTGRESQL" in db_opt:
                        pom_content += (
                            '    <dependency>\n'
                            '      <groupId>io.quarkus</groupId>\n'
                            '      <artifactId>quarkus-hibernate-orm-panache</artifactId>\n'
                            '    </dependency>\n'
                            '    <dependency>\n'
                            '      <groupId>io.quarkus</groupId>\n'
                            '      <artifactId>quarkus-jdbc-postgresql</artifactId>\n'
                            '    </dependency>\n'
                        )
                if "OUTBOX" in str(design_patterns):
                    pom_content += (
                        '    <dependency>\n'
                        '      <groupId>io.quarkus</groupId>\n'
                        '      <artifactId>quarkus-smallrye-reactive-messaging-kafka</artifactId>\n'
                        '    </dependency>\n'
                    )
                pom_content += (
                    '    <dependency>\n'
                    '      <groupId>io.quarkus</groupId>\n'
                    '      <artifactId>quarkus-junit5</artifactId>\n'
                    '      <scope>test</scope>\n'
                    '    </dependency>\n'
                    '    <dependency>\n'
                    '      <groupId>io.rest-assured</groupId>\n'
                    '      <artifactId>rest-assured</artifactId>\n'
                    '      <scope>test</scope>\n'
                    '    </dependency>\n'
                    '  </dependencies>\n\n'
                    '  <build>\n'
                    '    <plugins>\n'
                    '      <plugin>\n'
                    '        <groupId>${quarkus.platform.group-id}</groupId>\n'
                    '        <artifactId>quarkus-maven-plugin</artifactId>\n'
                    '        <version>${quarkus.platform.version}</version>\n'
                    '        <extensions>true</extensions>\n'
                    '        <executions>\n'
                    '          <execution>\n'
                    '            <goals>\n'
                    '              <goal>build</goal>\n'
                    '              <goal>generate-code</goal>\n'
                    '            </goals>\n'
                    '          </execution>\n'
                    '        </executions>\n'
                    '      </plugin>\n'
                    '    </plugins>\n'
                    '  </build>\n'
                    '</project>\n'
                )
                files_map["pom.xml"] = pom_content

            output = {"files": files_map}
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 3: Domain code generation prompt
        # -------------------------------------------------------------
        if "DOMAIN_CODE_NODE" in system_prompt:
            bp = _extract_blueprint_from_prompt(user_prompt)

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_pkg_path = effective_pkg.replace(".", "/")
            effective_entities = bp.get("entities", entities)
            effective_endpoints = bp.get("endpoints", custom_endpoints) or []
            db_opt = str(bp.get("database_option", db_opt)).upper()
            is_stateless = ("NONE" in db_opt or db_opt == "NONE")

            files = {}

            # 1. Global Exception Handler
            files[f"src/main/java/{effective_pkg_path}/exception/GlobalExceptionHandler.java"] = (
                f'package {effective_pkg}.exception;\n\n'
                'import io.quarkus.resteasy.reactive.server.ServerExceptionMapper;\n'
                'import jakarta.ws.rs.core.Response;\n'
                'import jakarta.ws.rs.NotFoundException;\n'
                'import java.net.URI;\n'
                'import java.util.Map;\n\n'
                'public class GlobalExceptionHandler {\n\n'
                '    @ServerExceptionMapper\n'
                '    public Response handleNotFound(NotFoundException ex) {\n'
                '        return Response.status(Response.Status.NOT_FOUND)\n'
                '            .entity(Map.of(\n'
                '                "type", "https://api.tcs.com/errors/not-found",\n'
                '                "title", "Recurso No Encontrado",\n'
                '                "status", 404,\n'
                '                "detail", ex.getMessage()\n'
                '            )).build();\n'
                '    }\n\n'
                '    @ServerExceptionMapper\n'
                '    public Response handleIllegalArgument(IllegalArgumentException ex) {\n'
                '        return Response.status(Response.Status.BAD_REQUEST)\n'
                '            .entity(Map.of(\n'
                '                "type", "https://api.tcs.com/errors/bad-request",\n'
                '                "title", "Parámetros Inválidos",\n'
                '                "status", 400,\n'
                '                "detail", ex.getMessage()\n'
                '            )).build();\n'
                '    }\n'
                '}\n'
            )

            # 2. Outbox Event Pattern if selected
            if "OUTBOX" in str(design_patterns):
                files[f"src/main/java/{effective_pkg_path}/outbox/OutboxEvent.java"] = (
                    f'package {effective_pkg}.outbox;\n\n'
                    'import java.time.LocalDateTime;\n'
                    'import java.util.UUID;\n\n'
                    'public record OutboxEvent(\n'
                    '    UUID id,\n'
                    '    String aggregateType,\n'
                    '    String aggregateId,\n'
                    '    String eventType,\n'
                    '    String payloadJson,\n'
                    '    LocalDateTime createdAt\n'
                    ') {\n'
                    '    public static OutboxEvent of(String type, String aggId, String payload) {\n'
                    '        return new OutboxEvent(UUID.randomUUID(), type, aggId, type + "_CREATED", payload, LocalDateTime.now());\n'
                    '    }\n'
                    '}\n'
                )

            # 3. Generate COMPLETE classes for EVERY entity defined by user!
            for ent in effective_entities:
                c_name = ent.get("name", "Account").capitalize()
                tbl_name = ent.get("tableName", f"{c_name.lower()}s")
                fields = ent.get("fields", [])
                lower_name = c_name.lower()

                # Java imports & fields declarations
                field_decls = []
                getters_setters = []
                for f in fields:
                    f_name = f.get("name")
                    f_type = f.get("type", "String")
                    if f_type == "Integer":
                        j_type = "Integer"
                    elif f_type in ["BigDecimal", "Currency", "Money"]:
                        j_type = "java.math.BigDecimal"
                    elif f_type in ["LocalDateTime", "Date", "Timestamp"]:
                        j_type = "java.time.LocalDateTime"
                    elif f_type in ["UUID", "uuid"]:
                        j_type = "java.util.UUID"
                    else:
                        j_type = "String"

                    is_id = f.get("isId", False) or f_name == "id"
                    if is_id and not is_stateless:
                        field_decls.append(f'    @Id\n    @GeneratedValue\n    private {j_type} {f_name};')
                    else:
                        field_decls.append(f'    @Column(name = "{f_name}")\n    private {j_type} {f_name};')

                    cap_name = f_name[0].upper() + f_name[1:]
                    getters_setters.append(f'    public {j_type} get{cap_name}() {{ return this.{f_name}; }}')
                    getters_setters.append(f'    public void set{cap_name}({j_type} {f_name}) {{ this.{f_name} = {f_name}; }}')

                # A. Entity class
                if is_stateless:
                    entity_code = (
                        f'package {effective_pkg}.domain;\n\n'
                        'import java.math.BigDecimal;\n'
                        'import java.time.LocalDateTime;\n'
                        'import java.util.UUID;\n\n'
                        f'public class {c_name} {{\n'
                        + '\n'.join(field_decls) + '\n\n'
                        f'    public {c_name}() {{}}\n\n'
                        + '\n'.join(getters_setters) + '\n'
                        '}\n'
                    )
                else:
                    entity_code = (
                        f'package {effective_pkg}.domain;\n\n'
                        'import jakarta.persistence.*;\n'
                        'import java.math.BigDecimal;\n'
                        'import java.time.LocalDateTime;\n'
                        'import java.util.UUID;\n\n'
                        '@Entity\n'
                        f'@Table(name = "{tbl_name}")\n'
                        f'public class {c_name} {{\n'
                        + '\n'.join(field_decls) + '\n\n'
                        f'    public {c_name}() {{}}\n\n'
                        + '\n'.join(getters_setters) + '\n'
                        '}\n'
                    )
                files[f"src/main/java/{effective_pkg_path}/domain/{c_name}.java"] = entity_code

                # B. DTO classes (RequestDTO & ResponseDTO)
                req_dto = (
                    f'package {effective_pkg}.dto;\n\n'
                    'import jakarta.validation.constraints.*;\n'
                    'import java.math.BigDecimal;\n'
                    'import java.util.UUID;\n\n'
                    f'public record {c_name}RequestDTO(\n'
                    f'    @NotBlank String referenceCode,\n'
                    f'    @NotNull @Positive BigDecimal amount,\n'
                    f'    String description\n'
                    ') {}\n'
                )
                res_dto = (
                    f'package {effective_pkg}.dto;\n\n'
                    'import java.math.BigDecimal;\n'
                    'import java.time.LocalDateTime;\n'
                    'import java.util.UUID;\n\n'
                    f'public record {c_name}ResponseDTO(\n'
                    f'    UUID id,\n'
                    f'    String referenceCode,\n'
                    f'    BigDecimal amount,\n'
                    f'    String status,\n'
                    f'    LocalDateTime timestamp\n'
                    ') {}\n'
                )
                files[f"src/main/java/{effective_pkg_path}/dto/{c_name}RequestDTO.java"] = req_dto
                files[f"src/main/java/{effective_pkg_path}/dto/{c_name}ResponseDTO.java"] = res_dto

                # C. Repository Panache
                if not is_stateless:
                    repo_code = (
                        f'package {effective_pkg}.repository;\n\n'
                        f'import {effective_pkg}.domain.{c_name};\n'
                        'import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n'
                        'import java.util.UUID;\n'
                        'import java.util.Optional;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {c_name}Repository implements PanacheRepositoryBase<{c_name}, UUID> {{\n'
                        f'    public Optional<{c_name}> findByReference(String code) {{\n'
                        '        return find("referenceCode", code).firstResultOptional();\n'
                        '    }}\n'
                        '}\n'
                    )
                    files[f"src/main/java/{effective_pkg_path}/repository/{c_name}Repository.java"] = repo_code

                # D. Service / UseCase
                service_code = (
                    f'package {effective_pkg}.service;\n\n'
                    f'import {effective_pkg}.domain.{c_name};\n'
                    f'import {effective_pkg}.dto.{c_name}RequestDTO;\n'
                    f'import {effective_pkg}.dto.{c_name}ResponseDTO;\n'
                    f'import {effective_pkg}.repository.{c_name}Repository;\n'
                    'import jakarta.enterprise.context.ApplicationScoped;\n'
                    'import jakarta.inject.Inject;\n'
                    'import jakarta.transaction.Transactional;\n'
                    'import jakarta.ws.rs.NotFoundException;\n'
                    'import java.time.LocalDateTime;\n'
                    'import java.util.List;\n'
                    'import java.util.UUID;\n\n'
                    '@ApplicationScoped\n'
                    f'public class {c_name}Service {{\n\n'
                    f'    @Inject\n    {c_name}Repository repository;\n\n'
                    f'    @Transactional\n'
                    f'    public {c_name}ResponseDTO create({c_name}RequestDTO request) {{\n'
                    f'        var entity = new {c_name}();\n'
                    '        entity.setId(UUID.randomUUID());\n'
                    '        entity.setStatus("APPROVED");\n'
                    '        repository.persist(entity);\n'
                    f'        return new {c_name}ResponseDTO(entity.getId(), request.referenceCode(), request.amount(), "APPROVED", LocalDateTime.now());\n'
                    '    }\n\n'
                    f'    public {c_name}ResponseDTO getById(UUID id) {{\n'
                    '        return repository.findByIdOptional(id)\n'
                    f'            .map(e -> new {c_name}ResponseDTO(e.getId(), "REF-100", java.math.BigDecimal.valueOf(100), "ACTIVE", LocalDateTime.now()))\n'
                    f'            .orElseThrow(() -> new NotFoundException("{c_name} con ID " + id + " no encontrado"));\n'
                    '    }\n\n'
                    f'    public List<{c_name}ResponseDTO> listAll() {{\n'
                    '        return repository.listAll().stream()\n'
                    f'            .map(e -> new {c_name}ResponseDTO(e.getId(), "REF-ALL", java.math.BigDecimal.TEN, "ACTIVE", LocalDateTime.now()))\n'
                    '            .toList();\n'
                    '    }}\n'
                    '}\n'
                )
                files[f"src/main/java/{effective_pkg_path}/service/{c_name}Service.java"] = service_code

                # E. Reactive REST Resource Controller
                resource_code = (
                    f'package {effective_pkg}.resource;\n\n'
                    f'import {effective_pkg}.dto.{c_name}RequestDTO;\n'
                    f'import {effective_pkg}.dto.{c_name}ResponseDTO;\n'
                    f'import {effective_pkg}.service.{c_name}Service;\n'
                    'import io.smallrye.mutiny.Uni;\n'
                    'import jakarta.annotation.security.RolesAllowed;\n'
                    'import jakarta.inject.Inject;\n'
                    'import jakarta.validation.Valid;\n'
                    'import jakarta.ws.rs.*;\n'
                    'import jakarta.ws.rs.core.MediaType;\n'
                    'import jakarta.ws.rs.core.Response;\n'
                    'import org.eclipse.microprofile.openapi.annotations.Operation;\n'
                    'import org.eclipse.microprofile.openapi.annotations.responses.APIResponse;\n'
                    'import java.net.URI;\n'
                    'import java.util.List;\n'
                    'import java.util.UUID;\n\n'
                    f'@Path("/api/v1/{lower_name}s")\n'
                    '@Produces(MediaType.APPLICATION_JSON)\n'
                    '@Consumes(MediaType.APPLICATION_JSON)\n'
                    f'public class {c_name}Resource {{\n\n'
                    f'    @Inject\n    {c_name}Service service;\n\n'
                    f'    @POST\n'
                    f'    @Operation(summary = "Registrar nuevo {c_name} transaccional")\n'
                    '    @APIResponse(responseCode = "201", description = "Recurso creado con éxito")\n'
                    '    @APIResponse(responseCode = "400", description = "Datos de entrada inválidos")\n'
                    '    @RolesAllowed({"ADMIN", "OPERATOR"})\n'
                    f'    public Uni<Response> create(@Valid {c_name}RequestDTO dto) {{\n'
                    '        return Uni.createFrom().item(() -> service.create(dto))\n'
                    f'            .map(res -> Response.created(URI.create("/api/v1/{lower_name}s/" + res.id())).entity(res).build());\n'
                    '    }\n\n'
                    f'    @GET\n    @Path("/{{id}}")\n'
                    f'    @Operation(summary = "Consultar {c_name} por UUID")\n'
                    '    @APIResponse(responseCode = "200", description = "Detalle del recurso")\n'
                    '    @APIResponse(responseCode = "404", description = "Recurso no encontrado")\n'
                    '    @RolesAllowed({"ADMIN", "OPERATOR", "AUDITOR"})\n'
                    '    public Uni<Response> getById(@PathParam("id") UUID id) {\n'
                    '        return Uni.createFrom().item(() -> service.getById(id))\n'
                    '            .map(res -> Response.ok(res).build());\n'
                    '    }\n\n'
                    f'    @GET\n'
                    f'    @Operation(summary = "Listar {c_name}s activos")\n'
                    '    @RolesAllowed({"ADMIN", "OPERATOR", "AUDITOR"})\n'
                    f'    public Uni<List<{c_name}ResponseDTO>> listAll() {{\n'
                    '        return Uni.createFrom().item(() -> service.listAll());\n'
                    '    }\n'
                    '}\n'
                )
                files[f"src/main/java/{effective_pkg_path}/resource/{c_name}Resource.java"] = resource_code

            output = {"files": files}
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 4: Tests generation prompt
        # -------------------------------------------------------------
        if "TESTS_NODE" in system_prompt:
            bp = _extract_blueprint_from_prompt(user_prompt)

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_pkg_path = effective_pkg.replace(".", "/")
            effective_entities = bp.get("entities", entities)

            test_files = {}
            for ent in effective_entities:
                c_name = ent.get("name", "Account").capitalize()
                lower_name = c_name.lower()

                test_code = (
                    f'package {effective_pkg}.resource;\n\n'
                    'import io.quarkus.test.junit.QuarkusTest;\n'
                    'import io.quarkus.test.security.TestSecurity;\n'
                    'import io.restassured.http.ContentType;\n'
                    'import org.junit.jupiter.api.Test;\n\n'
                    'import static io.restassured.RestAssured.given;\n'
                    'import static org.hamcrest.CoreMatchers.*;\n\n'
                    '@QuarkusTest\n'
                    f'public class {c_name}ResourceTest {{\n\n'
                    '    @Test\n'
                    '    @TestSecurity(user = "adminUser", roles = {"ADMIN"})\n'
                    f'    public void testCreate{c_name}() {{\n'
                    '        String payload = """\n'
                    '            {\n'
                    '                "referenceCode": "TEST-2026-001",\n'
                    '                "amount": 5000.00,\n'
                    '                "description": "Prueba de validación Quarkus"\n'
                    '            }\n'
                    '        """;\n\n'
                    '        given()\n'
                    '            .contentType(ContentType.JSON)\n'
                    '            .body(payload)\n'
                    '            .when()\n'
                    f'            .post("/api/v1/{lower_name}s")\n'
                    '            .then()\n'
                    '            .statusCode(anyOf(is(201), is(200)))\n'
                    '            .body("status", notNullValue());\n'
                    '    }\n\n'
                    '    @Test\n'
                    '    @TestSecurity(user = "auditorUser", roles = {"AUDITOR"})\n'
                    f'    public void testList{c_name}s() {{\n'
                    '        given()\n'
                    '            .when()\n'
                    f'            .get("/api/v1/{lower_name}s")\n'
                    '            .then()\n'
                    '            .statusCode(200);\n'
                    '    }\n'
                    '}\n'
                )
                test_files[f"src/test/java/{effective_pkg_path}/resource/{c_name}ResourceTest.java"] = test_code

            output = {"files": test_files}
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        return "{}", prompt_tokens, 0
