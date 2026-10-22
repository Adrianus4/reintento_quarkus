"""
Universal Capability Catalog for TCS Quarkus Factory.
Resolves all inbound, outbound, and non-functional requirements into official Quarkus 3.15 extensions.
Guarantees:
- Versions managed EXCLUSIVELY via Quarkus BOM.
- Deterministic multi-profile application.properties (%dev, %test, %prod).
- Test scope dependencies automatically resolved (JUnit 5, Mockito, H2, RestAssured, SmallRye JWT Build).
"""

from typing import Any, Dict, List, Set
from app.capabilities.base import CapabilityDescriptor, MavenCoordinate


class CapabilityCatalog:

    @classmethod
    def get_standard_dependencies(cls, client_code: str) -> List[MavenCoordinate]:
        """Base Quarkus 3.15 enterprise dependencies required across all microservices."""
        deps = [
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-resteasy-reactive-jackson"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-hibernate-validator"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-openapi"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-health"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-jwt"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-micrometer-registry-prometheus"),
            # Test Scope dependencies
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-junit5", scope="test"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-junit5-mockito", scope="test"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-test-security-jwt", scope="test"),
            MavenCoordinate(group_id="io.rest-assured", artifact_id="rest-assured", scope="test"),
            MavenCoordinate(group_id="io.smallrye", artifact_id="smallrye-jwt-build", scope="test"),
            MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-jdbc-h2", scope="test"),
        ]
        return deps

    @classmethod
    def resolve_capabilities(cls, spec: Dict[str, Any]) -> List[MavenCoordinate]:
        """Resolve all capabilities requested in ServiceSpec into Maven coordinates."""
        client_code = spec.get("governance_ref", {}).get("client_code", "bcp").lower()
        coords: List[MavenCoordinate] = cls.get_standard_dependencies(client_code)
        seen_artifacts: Set[str] = {c.artifact_id for c in coords}

        # Check outbounds
        for ob in spec.get("outbound", []):
            kind = ob.get("kind", "")
            if kind == "database":
                db_type = ob.get("details", {}).get("db_type", "").lower()
                if "sqlserver" in db_type or "mssql" in db_type:
                    db_art = "quarkus-jdbc-mssql"
                else:
                    db_art = "quarkus-jdbc-postgresql"

                for art in ["quarkus-hibernate-orm-panache", db_art]:
                    if art not in seen_artifacts:
                        coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id=art))
                        seen_artifacts.add(art)

            elif kind in ["kafka_producer", "kafka_consumer"]:
                if "quarkus-smallrye-reactive-messaging-kafka" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-reactive-messaging-kafka"))
                    seen_artifacts.add("quarkus-smallrye-reactive-messaging-kafka")

            elif kind == "rest_client":
                if "quarkus-rest-client-reactive-jackson" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-rest-client-reactive-jackson"))
                    seen_artifacts.add("quarkus-rest-client-reactive-jackson")

            elif kind == "cache":
                if "quarkus-redis-client" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-redis-client"))
                    seen_artifacts.add("quarkus-redis-client")

            elif kind == "grpc_client":
                if "quarkus-grpc" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-grpc"))
                    seen_artifacts.add("quarkus-grpc")

        # Check inbounds
        for ib in spec.get("inbound", []):
            kind = ib.get("kind", "")
            if kind == "scheduler":
                if "quarkus-scheduler" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-scheduler"))
                    seen_artifacts.add("quarkus-scheduler")
            elif kind == "graphql":
                if "quarkus-smallrye-graphql" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-graphql"))
                    seen_artifacts.add("quarkus-smallrye-graphql")
            elif kind == "grpc":
                if "quarkus-grpc" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-grpc"))
                    seen_artifacts.add("quarkus-grpc")

        # Check non_functional resilience
        nf = spec.get("non_functional", {})
        if isinstance(nf, dict):
            resil = nf.get("resilience", {})
            if isinstance(resil, dict):
                needs_ft = bool(resil.get("circuit_breaker") or resil.get("retry"))
            else:
                needs_ft = bool(resil and str(resil).lower() not in ["none", ""])
            if needs_ft:
                if "quarkus-smallrye-fault-tolerance" not in seen_artifacts:
                    coords.append(MavenCoordinate(group_id="io.quarkus", artifact_id="quarkus-smallrye-fault-tolerance"))
                    seen_artifacts.add("quarkus-smallrye-fault-tolerance")

        return coords

    @classmethod
    def assemble_pom_xml(cls, spec: Dict[str, Any]) -> str:
        """
        Deterministically assemble the complete pom.xml.
        Strict Enterprise Rule: Versions are managed EXCLUSIVELY by the Quarkus BOM.
        """
        gov = spec.get("governance_ref", {})
        service = spec.get("service", {})
        client_code = gov.get("client_code", "bcp").lower()
        artifact_id = service.get("name", f"{client_code}-service").lower().replace(" ", "-")
        group_id = gov.get("package_prefix", f"pe.com.{client_code}")
        quarkus_version = gov.get("quarkus_version", "3.15.1")
        java_version = gov.get("java_version", "21")

        deps = cls.resolve_capabilities(spec)

        dep_xml_blocks = []
        for d in deps:
            scope_tag = f"\n      <scope>{d.scope}</scope>" if d.scope else ""
            dep_xml_blocks.append(f"""    <dependency>
      <groupId>{d.group_id}</groupId>
      <artifactId>{d.artifact_id}</artifactId>{scope_tag}
    </dependency>""")

        dependencies_str = "\n".join(dep_xml_blocks)

        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>{group_id}</groupId>
  <artifactId>{artifact_id}</artifactId>
  <version>1.0.0-SNAPSHOT</version>

  <properties>
    <compiler-plugin.version>3.13.0</compiler-plugin.version>
    <maven.compiler.release>{java_version}</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
    <quarkus.platform.artifact-id>quarkus-bom</quarkus.platform.artifact-id>
    <quarkus.platform.group-id>io.quarkus.platform</quarkus.platform.group-id>
    <quarkus.platform.version>{quarkus_version}</quarkus.platform.version>
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
{dependencies_str}
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
          <compilerArgs>
            <arg>-parameters</arg>
          </compilerArgs>
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
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""
        return pom_content

    @classmethod
    def assemble_application_properties(cls, spec: Dict[str, Any]) -> str:
        """Deterministically assemble multi-profile application.properties (%dev, %test, %prod)."""
        gov = spec.get("governance_ref", {})
        client_code = gov.get("client_code", "bcp").lower()
        artifact_id = spec.get("service", {}).get("name", f"{client_code}-microservice")

        db_kind = "postgresql"
        for ob in spec.get("outbound", []):
            if ob.get("kind") == "database":
                t = ob.get("details", {}).get("db_type", "") or ob.get("details", {}).get("type", "")
                if "mssql" in t.lower() or "sqlserver" in t.lower():
                    db_kind = "mssql"
                elif "postgres" in t.lower():
                    db_kind = "postgresql"

        prod_jdbc_url = (
            f"jdbc:sqlserver://localhost:1433;databaseName={client_code}_db;encrypt=false"
            if db_kind == "mssql"
            else f"jdbc:postgresql://localhost:5432/{client_code}_db"
        )

        props = f"""# ==============================================================================
# TCS QUARKUS FACTORY - DETERMINISTIC MULTI-PROFILE CONFIGURATION
# Client: {client_code.upper()} | Generated for Enterprise Governance
# ==============================================================================

quarkus.http.port=8080
quarkus.http.cors=true
quarkus.log.level=INFO
quarkus.application.name={artifact_id}

# SmallRye OpenAPI & Health
quarkus.smallrye-openapi.path=/q/openapi
quarkus.swagger-ui.always-include=true
quarkus.smallrye-health.root-path=/q/health

# ==============================================================================
# LOCAL DEVELOPMENT & ISOLATED TESTING (%dev, %test)
# In-memory H2 database ensures zero external dependencies for dev/test execution
# ==============================================================================
# Local Dev Profile
%dev.quarkus.datasource.db-kind=h2
%dev.quarkus.datasource.jdbc.url=jdbc:h2:mem:devdb;DB_CLOSE_DELAY=-1
%dev.quarkus.datasource.username=sa
%dev.quarkus.datasource.password=sa
%dev.quarkus.hibernate-orm.database.generation=drop-and-create
%dev.quarkus.hibernate-orm.sql-load-script=import.sql
%dev.mp.jwt.verify.publickey.location=publicKey.pem
%dev.quarkus.kafka.devservices.enabled=false

# Test Profile
%test.quarkus.datasource.db-kind=h2
%test.quarkus.datasource.jdbc.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1
%test.quarkus.datasource.username=sa
%test.quarkus.datasource.password=sa
%test.quarkus.hibernate-orm.database.generation=drop-and-create
%test.quarkus.hibernate-orm.sql-load-script=import.sql
%test.mp.jwt.verify.publickey.location=publicKey.pem
%test.quarkus.kafka.devservices.enabled=false

# ==============================================================================
# ENTERPRISE PRODUCTION (%prod)
# Production configuration utilizing secure environment variables
# ==============================================================================
%prod.quarkus.datasource.db-kind={db_kind}
%prod.quarkus.datasource.jdbc.url=${{DB_URL:{prod_jdbc_url}}}
%prod.quarkus.datasource.username=${{DB_USER:{client_code}_app}}
%prod.quarkus.datasource.password=${{DB_PASSWORD:secret}}
%prod.quarkus.hibernate-orm.database.generation=validate
%prod.mp.jwt.verify.issuer=${{JWT_ISSUER:https://auth.via{client_code}.com}}
%prod.mp.jwt.verify.publickey.location=${{JWT_PUBLIC_KEY_LOCATION:publicKey.pem}}
"""
        return props
