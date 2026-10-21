import json
import re
from typing import Any, Dict, List, Tuple
from app.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Deterministic offline mock provider producing valid, customized Quarkus microservices."""

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

        # Extract client, package, architecture, security, database
        client_code = self._extract_param(user_prompt, "Client Code:", "ibk").lower()
        default_pkg = "pe.com.interbank" if "ibk" in client_code else ("pe.com.bcp" if "bcp" in client_code else f"pe.com.{client_code}")
        
        user_pkg = self._extract_param(user_prompt, "User Package Prefix:", "")
        package_prefix = user_pkg if (user_pkg and user_pkg != "None") else default_pkg

        raw_arch = self._extract_param(user_prompt, "User Architecture Selection:", "Hexagonal")
        if "hex" in raw_arch.lower():
            arch_style = "Hexagonal"
        elif "layer" in raw_arch.lower():
            arch_style = "Layered"
        elif "event" in raw_arch.lower():
            arch_style = "Event-Driven"
        else:
            arch_style = raw_arch.capitalize()

        security_opt = self._extract_param(user_prompt, "User Security Selection:", "JWT").upper()
        db_opt = self._extract_param(user_prompt, "User Database Selection:", "POSTGRESQL_PANACHE").upper()
        artifact_id = self._extract_param(user_prompt, "User Artifact ID:", f"{client_code}-microservice")
        if not artifact_id or artifact_id == "None":
            artifact_id = f"{client_code}-microservice"
        http_port = self._extract_param(user_prompt, "User HTTP Port:", "8080")
        if not http_port or http_port == "None":
            http_port = "8080"
        database_name = self._extract_param(user_prompt, "User Database Name:", f"{client_code}_db")
        if not database_name or database_name == "None":
            database_name = f"{client_code}_db"

        custom_endpoints = self._extract_json_field(user_prompt, "User Custom Endpoints")
        custom_extensions = self._extract_json_field(user_prompt, "User Custom Free Extensions")
        custom_properties = self._extract_json_field(user_prompt, "User Custom Properties")

        user_entities = self._extract_json_field(user_prompt, "User Defined Entities")
        if not user_entities or not isinstance(user_entities, list) or len(user_entities) == 0:
            if "ibk" in client_code:
                entity_name = "Transfer"
                fields = [
                    {"name": "id", "type": "String", "required": True},
                    {"name": "sourceAccount", "type": "String", "required": True},
                    {"name": "destinationAccount", "type": "String", "required": True},
                    {"name": "amount", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                ]
            else:
                entity_name = "Account"
                fields = [
                    {"name": "id", "type": "String", "required": True},
                    {"name": "balance", "type": "BigDecimal", "required": True},
                    {"name": "status", "type": "String", "required": True},
                ]
            entities = [{"name": entity_name, "fields": fields}]
        else:
            entities = user_entities

        primary_entity = entities[0]
        entity_name = primary_entity.get("name", "Account")
        pkg_path = package_prefix.replace(".", "/")

        # -------------------------------------------------------------
        # Node 1: Blueprint design prompt
        # -------------------------------------------------------------
        if "BLUEPRINT_DESIGN_NODE" in system_prompt:
            dependencies = [
                "quarkus-resteasy-reactive-jackson",
                "quarkus-smallrye-openapi",
                "quarkus-hibernate-validator",
            ]
            if "JWT" in security_opt:
                dependencies.append("quarkus-smallrye-jwt")
            elif "OIDC" in security_opt:
                dependencies.append("quarkus-oidc")

            is_stateless = ("NONE" in db_opt or db_opt == "NONE")
            if not is_stateless:
                if "POSTGRESQL" in db_opt:
                    dependencies.extend(["quarkus-hibernate-orm-panache", "quarkus-jdbc-postgresql"])
                elif "MYSQL" in db_opt:
                    dependencies.extend(["quarkus-hibernate-orm-panache", "quarkus-jdbc-mysql"])
                elif "MONGODB" in db_opt:
                    dependencies.append("quarkus-mongodb-panache")

            if custom_extensions and isinstance(custom_extensions, list):
                for ext in custom_extensions:
                    if ext and ext not in dependencies:
                        dependencies.append(ext.strip())

            endpoints_list = []
            if custom_endpoints and isinstance(custom_endpoints, list) and len(custom_endpoints) > 0:
                for ep in custom_endpoints:
                    endpoints_list.append({
                        "path": ep.get("path", f"/api/v1/{entity_name.lower()}s"),
                        "method": ep.get("method", "GET"),
                        "summary": ep.get("summary", "Operación configurada"),
                    })
            else:
                endpoints_list = [
                    {
                        "path": f"/api/v1/{entity_name.lower()}s",
                        "method": "POST",
                        "summary": f"Create or register new {entity_name}"
                    },
                    {
                        "path": f"/api/v1/{entity_name.lower()}s/{{id}}",
                        "method": "GET",
                        "summary": f"Fetch {entity_name} by ID"
                    }
                ]

            output = {
                "architecture_style": arch_style,
                "artifact_id": artifact_id,
                "quarkus_version": "3.15.1",
                "java_version": "21" if "ibk" in client_code else "17",
                "package_prefix": package_prefix,
                "dependencies": dependencies,
                "entities": entities,
                "endpoints": endpoints_list,
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 2: Scaffolding generation prompt
        # -------------------------------------------------------------
        if "SCAFFOLDING_NODE" in system_prompt:
            bp_match = re.search(r"Blueprint:\s*(\{.*?\})", user_prompt, re.DOTALL)
            bp = {}
            if bp_match:
                try:
                    bp = json.loads(bp_match.group(1))
                except Exception:
                    pass

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_java = bp.get("java_version", "21")
            effective_artifact = bp.get("artifact_id", artifact_id)

            deps_xml = [
                '    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-resteasy-reactive-jackson</artifactId>\n    </dependency>',
                '    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-smallrye-openapi</artifactId>\n    </dependency>',
                '    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-hibernate-validator</artifactId>\n    </dependency>',
                '    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-smallrye-health</artifactId>\n    </dependency>',
                '    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-micrometer-registry-prometheus</artifactId>\n    </dependency>',
            ]

            if "JWT" in security_opt or "jwt" in str(bp.get("dependencies", [])):
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-smallrye-jwt</artifactId>\n    </dependency>')
            elif "OIDC" in security_opt:
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-oidc</artifactId>\n    </dependency>')

            if "POSTGRESQL" in db_opt or "postgresql" in str(bp.get("dependencies", [])):
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-hibernate-orm-panache</artifactId>\n    </dependency>')
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-jdbc-postgresql</artifactId>\n    </dependency>')
            elif "MYSQL" in db_opt:
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-hibernate-orm-panache</artifactId>\n    </dependency>')
                deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-jdbc-mysql</artifactId>\n    </dependency>')

            # Add custom user extensions
            if custom_extensions and isinstance(custom_extensions, list):
                for ext in custom_extensions:
                    if ext and ext.strip():
                        name = ext.strip()
                        if ":" in name:
                            parts = name.split(":")
                            deps_xml.append(f'    <dependency>\n      <groupId>{parts[0]}</groupId>\n      <artifactId>{parts[1]}</artifactId>\n    </dependency>')
                        else:
                            deps_xml.append(f'    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>{name}</artifactId>\n    </dependency>')

            deps_xml.append('    <dependency>\n      <groupId>io.quarkus</groupId>\n      <artifactId>quarkus-junit5</artifactId>\n      <scope>test</scope>\n    </dependency>')
            deps_xml.append('    <dependency>\n      <groupId>io.rest-assured</groupId>\n      <artifactId>rest-assured</artifactId>\n      <scope>test</scope>\n    </dependency>')

            pom_content = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<project xmlns="http://maven.apache.org/POM/4.0.0"\n'
                '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">\n'
                '  <modelVersion>4.0.0</modelVersion>\n'
                f'  <groupId>{effective_pkg}</groupId>\n'
                f'  <artifactId>{effective_artifact}</artifactId>\n'
                '  <version>1.0.0-SNAPSHOT</version>\n'
                '  <properties>\n'
                '    <compiler-plugin.version>3.13.0</compiler-plugin.version>\n'
                f'    <maven.compiler.release>{effective_java}</maven.compiler.release>\n'
                '    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>\n'
                '    <quarkus.platform.artifact-id>quarkus-bom</quarkus.platform.artifact-id>\n'
                '    <quarkus.platform.group-id>io.quarkus.platform</quarkus.platform.group-id>\n'
                '    <quarkus.platform.version>3.15.1</quarkus.platform.version>\n'
                '  </properties>\n'
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
                '  </dependencyManagement>\n'
                '  <dependencies>\n' + '\n'.join(deps_xml) + '\n  </dependencies>\n'
                '</project>\n'
            )

            props_content = (
                f'# Quarkus Configuration - Client: {client_code.upper()}\n'
                f'quarkus.application.name={effective_artifact}\n'
                f'quarkus.http.port={http_port}\n'
                'quarkus.http.cors=true\n'
                '# Observability\n'
                'quarkus.smallrye-openapi.path=/q/openapi\n'
                'quarkus.swagger-ui.always-include=true\n'
            )

            if "POSTGRESQL" in db_opt:
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
                    '\n# Security (SmallRye JWT)\n'
                    'mp.jwt.verify.issuer=https://auth.tcs-factory.com\n'
                    'mp.jwt.verify.publickey.location=META-INF/resources/publicKey.pem\n'
                )

            # Ingest custom properties entered by user
            if custom_properties:
                props_content += "\n# User Custom Properties\n"
                if isinstance(custom_properties, dict):
                    for k, v in custom_properties.items():
                        props_content += f"{k}={v}\n"
                elif isinstance(custom_properties, str):
                    props_content += f"{custom_properties.strip()}\n"

            ci_content = (
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
                '      - run: mvn -B clean test\n'
            )

            output = {
                "files": {
                    "pom.xml": pom_content,
                    "src/main/resources/application.properties": props_content,
                    ".github/workflows/ci.yml": ci_content,
                }
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 3: Domain code generation prompt
        # -------------------------------------------------------------
        if "DOMAIN_CODE_NODE" in system_prompt:
            bp_match = re.search(r"Blueprint:\s*(\{.*?\})", user_prompt, re.DOTALL)
            bp = {}
            if bp_match:
                try:
                    bp = json.loads(bp_match.group(1))
                except Exception:
                    pass

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_pkg_path = effective_pkg.replace(".", "/")
            effective_arch = bp.get("architecture_style", arch_style).upper()
            db_opt = str(bp.get("database_option", "NONE")).upper()
            is_stateless = ("NONE" in db_opt or db_opt == "NONE" or not bp.get("database_option"))

            entity_class = entity_name.capitalize()
            lower_name = entity_class.lower()

            files = {}

            if "LAYERED" in effective_arch:
                # Clean Layered Architecture
                if is_stateless:
                    # 100% Stateless Layered: No Panache, no Hibernate ORM, no DataSource
                    model_code = (
                        f'package {effective_pkg}.model;\n\n'
                        'import java.math.BigDecimal;\n\n'
                        f'public class {entity_class} {{\n'
                        '    private String id;\n'
                        '    private BigDecimal amount;\n'
                        '    private String status;\n'
                        '    private String description;\n\n'
                        f'    public {entity_class}() {{}}\n\n'
                        f'    public {entity_class}(String id, BigDecimal amount, String status) {{\n'
                        '        this.id = id;\n'
                        '        this.amount = amount;\n'
                        '        this.status = status;\n'
                        '    }}\n\n'
                        '    public String getId() { return id; }\n'
                        '    public void setId(String id) { this.id = id; }\n'
                        '    public BigDecimal getAmount() { return amount; }\n'
                        '    public void setAmount(BigDecimal amount) { this.amount = amount; }\n'
                        '    public String getStatus() { return status; }\n'
                        '    public void setStatus(String status) { this.status = status; }\n'
                        '    public String getDescription() { return description; }\n'
                        '    public void setDescription(String description) { this.description = description; }\n'
                        '}\n'
                    )
                    service_code = (
                        f'package {effective_pkg}.service;\n\n'
                        f'import {effective_pkg}.model.{entity_class};\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n'
                        'import java.math.BigDecimal;\n'
                        'import java.util.Optional;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {entity_class}Service {{\n'
                        f'    public Optional<{entity_class}> findById(String id) {{\n'
                        f'        return Optional.of(new {entity_class}(id, new BigDecimal("250.00"), "COMPLETED"));\n'
                        '    }}\n\n'
                        f'    public {entity_class} create({entity_class} entity) {{\n'
                        '        return entity;\n'
                        '    }}\n'
                        '}\n'
                    )
                    controller_code = (
                        f'package {effective_pkg}.controller;\n\n'
                        f'import {effective_pkg}.model.{entity_class};\n'
                        f'import {effective_pkg}.service.{entity_class}Service;\n'
                        'import jakarta.inject.Inject;\n'
                        'import jakarta.ws.rs.*;\n'
                        'import jakarta.ws.rs.core.MediaType;\n'
                        'import jakarta.ws.rs.core.Response;\n'
                        'import java.net.URI;\n\n'
                        f'@Path("/api/v1/{lower_name}s")\n'
                        '@Produces(MediaType.APPLICATION_JSON)\n'
                        '@Consumes(MediaType.APPLICATION_JSON)\n'
                        f'public class {entity_class}Resource {{\n'
                        '    @Inject\n'
                        f'    {entity_class}Service service;\n\n'
                        '    @GET\n'
                        '    @Path("/{id}")\n'
                        '    public Response getById(@PathParam("id") String id) {\n'
                        '        return service.findById(id)\n'
                        '            .map(Response::ok)\n'
                        '            .orElse(Response.status(Response.Status.NOT_FOUND))\n'
                        '            .build();\n'
                        '    }\n\n'
                        '    @POST\n'
                        f'    public Response create({entity_class} entity) {{\n'
                        '        var created = service.create(entity);\n'
                        f'        String id = created.getId() != null ? created.getId() : "item-1";\n'
                        f'        return Response.created(URI.create("/api/v1/{lower_name}s/" + id))\n'
                        '            .entity(created)\n'
                        '            .build();\n'
                        '    }}\n'
                        '}\n'
                    )
                    files[f"src/main/java/{effective_pkg_path}/model/{entity_class}.java"] = model_code
                    files[f"src/main/java/{effective_pkg_path}/service/{entity_class}Service.java"] = service_code
                    files[f"src/main/java/{effective_pkg_path}/controller/{entity_class}Resource.java"] = controller_code

                else:
                    # Stateful Layered Architecture (with Panache / Hibernate)
                    model_code = (
                        f'package {effective_pkg}.model;\n\n'
                        'import java.math.BigDecimal;\n'
                        'import jakarta.persistence.*;\n\n'
                        '@Entity\n'
                        f'@Table(name = "{lower_name}s")\n'
                        f'public class {entity_class} {{\n'
                        '    @Id\n'
                        '    @GeneratedValue(strategy = GenerationType.UUID)\n'
                        '    private String id;\n'
                        '    private BigDecimal amount;\n'
                        '    private String status;\n'
                        '    private String description;\n\n'
                        f'    public {entity_class}() {{}}\n\n'
                        f'    public {entity_class}(String id, BigDecimal amount, String status) {{\n'
                        '        this.id = id;\n'
                        '        this.amount = amount;\n'
                        '        this.status = status;\n'
                        '    }}\n\n'
                        '    public String getId() { return id; }\n'
                        '    public void setId(String id) { this.id = id; }\n'
                        '    public BigDecimal getAmount() { return amount; }\n'
                        '    public void setAmount(BigDecimal amount) { this.amount = amount; }\n'
                        '    public String getStatus() { return status; }\n'
                        '    public void setStatus(String status) { this.status = status; }\n'
                        '    public String getDescription() { return description; }\n'
                        '    public void setDescription(String description) { this.description = description; }\n'
                        '}\n'
                    )
                    repo_code = (
                        f'package {effective_pkg}.repository;\n\n'
                        f'import {effective_pkg}.model.{entity_class};\n'
                        'import io.quarkus.hibernate.orm.panache.PanacheRepositoryBase;\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {entity_class}Repository implements PanacheRepositoryBase<{entity_class}, String> {{\n'
                        '}\n'
                    )
                    service_code = (
                        f'package {effective_pkg}.service;\n\n'
                        f'import {effective_pkg}.model.{entity_class};\n'
                        f'import {effective_pkg}.repository.{entity_class}Repository;\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n'
                        'import jakarta.inject.Inject;\n'
                        'import jakarta.transaction.Transactional;\n'
                        'import java.util.Optional;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {entity_class}Service {{\n'
                        '    @Inject\n'
                        f'    {entity_class}Repository repository;\n\n'
                        f'    public Optional<{entity_class}> findById(String id) {{\n'
                        '        return repository.findByIdOptional(id);\n'
                        '    }}\n\n'
                        '    @Transactional\n'
                        f'    public {entity_class} create({entity_class} entity) {{\n'
                        '        repository.persist(entity);\n'
                        '        return entity;\n'
                        '    }}\n'
                        '}\n'
                    )
                    controller_code = (
                        f'package {effective_pkg}.controller;\n\n'
                        f'import {effective_pkg}.model.{entity_class};\n'
                        f'import {effective_pkg}.service.{entity_class}Service;\n'
                        'import jakarta.inject.Inject;\n'
                        'import jakarta.ws.rs.*;\n'
                        'import jakarta.ws.rs.core.MediaType;\n'
                        'import jakarta.ws.rs.core.Response;\n'
                        'import java.net.URI;\n\n'
                        f'@Path("/api/v1/{lower_name}s")\n'
                        '@Produces(MediaType.APPLICATION_JSON)\n'
                        '@Consumes(MediaType.APPLICATION_JSON)\n'
                        f'public class {entity_class}Resource {{\n'
                        '    @Inject\n'
                        f'    {entity_class}Service service;\n\n'
                        '    @GET\n'
                        '    @Path("/{id}")\n'
                        '    public Response getById(@PathParam("id") String id) {\n'
                        '        return service.findById(id)\n'
                        '            .map(Response::ok)\n'
                        '            .orElse(Response.status(Response.Status.NOT_FOUND))\n'
                        '            .build();\n'
                        '    }\n\n'
                        '    @POST\n'
                        f'    public Response create({entity_class} entity) {{\n'
                        '        var created = service.create(entity);\n'
                        f'        return Response.created(URI.create("/api/v1/{lower_name}s/" + created.getId()))\n'
                        '            .entity(created)\n'
                        '            .build();\n'
                        '    }}\n'
                        '}\n'
                    )
                    files[f"src/main/java/{effective_pkg_path}/model/{entity_class}.java"] = model_code
                    files[f"src/main/java/{effective_pkg_path}/repository/{entity_class}Repository.java"] = repo_code
                    files[f"src/main/java/{effective_pkg_path}/service/{entity_class}Service.java"] = service_code
                    files[f"src/main/java/{effective_pkg_path}/controller/{entity_class}Resource.java"] = controller_code

            else:
                # Hexagonal Architecture (Ports & Adapters)
                domain_model = (
                    f'package {effective_pkg}.domain.model;\n\n'
                    'import java.math.BigDecimal;\n\n'
                    f'public class {entity_class} {{\n'
                    '    private String id;\n'
                    '    private BigDecimal amount;\n'
                    '    private String status;\n\n'
                    f'    public {entity_class}(String id, BigDecimal amount, String status) {{\n'
                    '        this.id = id;\n'
                    '        this.amount = amount;\n'
                    '        this.status = status;\n'
                    '    }}\n\n'
                    '    public String getId() { return id; }\n'
                    '    public BigDecimal getAmount() { return amount; }\n'
                    '    public String getStatus() { return status; }\n'
                    '}\n'
                )
                use_case_port = (
                    f'package {effective_pkg}.domain.port.in;\n\n'
                    f'import {effective_pkg}.domain.model.{entity_class};\n'
                    'import java.util.Optional;\n\n'
                    f'public interface {entity_class}UseCase {{\n'
                    f'    Optional<{entity_class}> getById(String id);\n'
                    f'    {entity_class} execute({entity_class} entity);\n'
                    '}\n'
                )
                rest_adapter = (
                    f'package {effective_pkg}.infrastructure.adapter.in.rest;\n\n'
                    f'import {effective_pkg}.domain.model.{entity_class};\n'
                    f'import {effective_pkg}.domain.port.in.{entity_class}UseCase;\n'
                    'import jakarta.inject.Inject;\n'
                    'import jakarta.ws.rs.*;\n'
                    'import jakarta.ws.rs.core.MediaType;\n'
                    'import jakarta.ws.rs.core.Response;\n'
                    'import java.math.BigDecimal;\n\n'
                    f'@Path("/api/v1/{lower_name}s")\n'
                    '@Produces(MediaType.APPLICATION_JSON)\n'
                    '@Consumes(MediaType.APPLICATION_JSON)\n'
                    f'public class {entity_class}Resource {{\n'
                    '    @Inject\n'
                    f'    {entity_class}UseCase useCase;\n\n'
                    '    @GET\n'
                    '    @Path("/{id}")\n'
                    '    public Response getById(@PathParam("id") String id) {\n'
                    '        return useCase.getById(id)\n'
                    '            .map(Response::ok)\n'
                    '            .orElse(Response.status(Response.Status.NOT_FOUND))\n'
                    '            .build();\n'
                    '    }\n'
                    '}\n'
                )

                if is_stateless:
                    # 100% Stateless Hexagonal: Pure application service without database repository port
                    app_service = (
                        f'package {effective_pkg}.application.service;\n\n'
                        f'import {effective_pkg}.domain.model.{entity_class};\n'
                        f'import {effective_pkg}.domain.port.in.{entity_class}UseCase;\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n'
                        'import java.math.BigDecimal;\n'
                        'import java.util.Optional;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {entity_class}ApplicationService implements {entity_class}UseCase {{\n'
                        '    @Override\n'
                        f'    public Optional<{entity_class}> getById(String id) {{\n'
                        f'        return Optional.of(new {entity_class}(id, new BigDecimal("250.00"), "COMPLETED"));\n'
                        '    }}\n\n'
                        '    @Override\n'
                        f'    public {entity_class} execute({entity_class} entity) {{\n'
                        '        return entity;\n'
                        '    }}\n'
                        '}\n'
                    )
                    files[f"src/main/java/{effective_pkg_path}/domain/model/{entity_class}.java"] = domain_model
                    files[f"src/main/java/{effective_pkg_path}/domain/port/in/{entity_class}UseCase.java"] = use_case_port
                    files[f"src/main/java/{effective_pkg_path}/application/service/{entity_class}ApplicationService.java"] = app_service
                    files[f"src/main/java/{effective_pkg_path}/infrastructure/adapter/in/rest/{entity_class}Resource.java"] = rest_adapter

                else:
                    # Stateful Hexagonal: Includes Repository Port & DB Adapter
                    repo_port = (
                        f'package {effective_pkg}.domain.port.out;\n\n'
                        f'import {effective_pkg}.domain.model.{entity_class};\n'
                        'import java.util.Optional;\n\n'
                        f'public interface {entity_class}RepositoryPort {{\n'
                        f'    Optional<{entity_class}> findById(String id);\n'
                        f'    {entity_class} save({entity_class} entity);\n'
                        '}\n'
                    )
                    app_service = (
                        f'package {effective_pkg}.application.service;\n\n'
                        f'import {effective_pkg}.domain.model.{entity_class};\n'
                        f'import {effective_pkg}.domain.port.in.{entity_class}UseCase;\n'
                        f'import {effective_pkg}.domain.port.out.{entity_class}RepositoryPort;\n'
                        'import jakarta.enterprise.context.ApplicationScoped;\n'
                        'import jakarta.inject.Inject;\n'
                        'import java.util.Optional;\n\n'
                        '@ApplicationScoped\n'
                        f'public class {entity_class}ApplicationService implements {entity_class}UseCase {{\n'
                        '    @Inject\n'
                        f'    {entity_class}RepositoryPort repositoryPort;\n\n'
                        '    @Override\n'
                        f'    public Optional<{entity_class}> getById(String id) {{\n'
                        '        return repositoryPort.findById(id);\n'
                        '    }}\n\n'
                        '    @Override\n'
                        f'    public {entity_class} execute({entity_class} entity) {{\n'
                        '        return repositoryPort.save(entity);\n'
                        '    }}\n'
                        '}\n'
                    )
                    files[f"src/main/java/{effective_pkg_path}/domain/model/{entity_class}.java"] = domain_model
                    files[f"src/main/java/{effective_pkg_path}/domain/port/in/{entity_class}UseCase.java"] = use_case_port
                    files[f"src/main/java/{effective_pkg_path}/domain/port/out/{entity_class}RepositoryPort.java"] = repo_port
                    files[f"src/main/java/{effective_pkg_path}/application/service/{entity_class}ApplicationService.java"] = app_service
                    files[f"src/main/java/{effective_pkg_path}/infrastructure/adapter/in/rest/{entity_class}Resource.java"] = rest_adapter

            output = {"files": files}
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # -------------------------------------------------------------
        # Node 4: Tests generation prompt
        # -------------------------------------------------------------
        if "TESTS_NODE" in system_prompt:
            bp_match = re.search(r"Blueprint:\s*(\{.*?\})", user_prompt, re.DOTALL)
            bp = {}
            if bp_match:
                try:
                    bp = json.loads(bp_match.group(1))
                except Exception:
                    pass

            effective_pkg = bp.get("package_prefix", package_prefix)
            effective_pkg_path = effective_pkg.replace(".", "/")
            entity_class = entity_name.capitalize()
            lower_name = entity_class.lower()

            unit_test = (
                f'package {effective_pkg};\n\n'
                'import org.junit.jupiter.api.Test;\n'
                'import static org.junit.jupiter.api.Assertions.*;\n'
                'import java.math.BigDecimal;\n\n'
                f'public class {entity_class}UnitTest {{\n'
                '    @Test\n'
                f'    void test{entity_class}DomainValidation() {{\n'
                '        BigDecimal amount = new BigDecimal("250.00");\n'
                '        assertNotNull(amount);\n'
                '        assertTrue(amount.compareTo(BigDecimal.ZERO) > 0);\n'
                '    }}\n'
                '}\n'
            )

            api_test = (
                f'package {effective_pkg};\n\n'
                'import io.quarkus.test.junit.QuarkusTest;\n'
                'import org.junit.jupiter.api.Test;\n'
                'import static io.restassured.RestAssured.given;\n'
                'import static org.hamcrest.CoreMatchers.notNullValue;\n\n'
                '@QuarkusTest\n'
                f'public class {entity_class}ResourceTest {{\n'
                '    @Test\n'
                f'    void testGet{entity_class}Endpoint() {{\n'
                '        given()\n'
                f'          .when().get("/api/v1/{lower_name}s/txn-12345")\n'
                '          .then()\n'
                '             .statusCode(200)\n'
                '             .body("id", notNullValue());\n'
                '    }}\n'
                '}\n'
            )

            output = {
                "files": {
                    f"src/test/java/{effective_pkg_path}/{entity_class}UnitTest.java": unit_test,
                    f"src/test/java/{effective_pkg_path}/{entity_class}ResourceTest.java": api_test,
                }
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # Fallback
        fallback = {"status": "ok", "message": "Mock generation executed"}
        fallback_str = json.dumps(fallback)
        return fallback_str, prompt_tokens, len(fallback_str.split())
