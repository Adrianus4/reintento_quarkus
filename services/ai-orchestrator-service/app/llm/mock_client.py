import json
from typing import Tuple
from app.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Deterministic offline mock provider producing valid Quarkus structures."""

    def __init__(self, mode: str = "balanced"):
        self.mode = mode

    def test_connection(self) -> bool:
        return True

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> Tuple[str, int, int]:
        # Estimate simulated tokens
        prompt_tokens = len(system_prompt.split()) + len(user_prompt.split())

        # Node 1: Blueprint design prompt
        if "BLUEPRINT_DESIGN_NODE" in system_prompt:
            output = {
                "architecture_style": "Hexagonal",
                "quarkus_version": "3.15.1",
                "java_version": "17",
                "package_prefix": "com.tcs.factory.generated",
                "dependencies": [
                    "quarkus-resteasy-reactive-jackson",
                    "quarkus-smallrye-openapi",
                    "quarkus-hibernate-validator"
                ],
                "entities": [
                    {
                        "name": "Account",
                        "fields": [
                            {"name": "id", "type": "String", "required": True},
                            {"name": "balance", "type": "BigDecimal", "required": True},
                            {"name": "status", "type": "String", "required": True}
                        ]
                    }
                ],
                "endpoints": [
                    {
                        "path": "/api/v1/accounts",
                        "method": "POST",
                        "summary": "Create new account"
                    },
                    {
                        "path": "/api/v1/accounts/{id}",
                        "method": "GET",
                        "summary": "Fetch account details"
                    }
                ]
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # Node 2: Scaffolding generation prompt
        if "SCAFFOLDING_NODE" in system_prompt:
            output = {
                "files": {
                    "pom.xml": (
                        '<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
                        '  <modelVersion>4.0.0</modelVersion>\n'
                        '  <groupId>com.tcs.factory</groupId>\n'
                        '  <artifactId>generated-microservice</artifactId>\n'
                        '  <version>1.0.0-SNAPSHOT</version>\n'
                        '  <properties>\n'
                        '    <maven.compiler.release>17</maven.compiler.release>\n'
                        '    <quarkus.platform.version>3.15.1</quarkus.platform.version>\n'
                        '  </properties>\n'
                        '</project>\n'
                    ),
                    "src/main/resources/application.properties": (
                        'quarkus.http.port=8080\n'
                        'quarkus.application.name=generated-microservice\n'
                    ),
                    ".github/workflows/ci.yml": (
                        'name: Quarkus CI\n'
                        'on: [push, pull_request]\n'
                        'jobs:\n'
                        '  build:\n'
                        '    runs-on: ubuntu-latest\n'
                        '    steps:\n'
                        '      - uses: actions/checkout@v4\n'
                        '      - uses: actions/setup-java@v4\n'
                        '        with:\n'
                        '          java-version: "17"\n'
                        '          distribution: "temurin"\n'
                        '      - run: mvn -B clean test\n'
                    )
                }
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # Node 3: Domain code generation prompt
        if "DOMAIN_CODE_NODE" in system_prompt:
            output = {
                "files": {
                    "src/main/java/com/tcs/factory/domain/model/Account.java": (
                        'package com.tcs.factory.domain.model;\n\n'
                        'import java.math.BigDecimal;\n\n'
                        'public class Account {\n'
                        '    private String id;\n'
                        '    private BigDecimal balance;\n'
                        '    private String status;\n\n'
                        '    public Account(String id, BigDecimal balance, String status) {\n'
                        '        this.id = id;\n'
                        '        this.balance = balance;\n'
                        '        this.status = status;\n'
                        '    }\n'
                        '    public String getId() { return id; }\n'
                        '    public BigDecimal getBalance() { return balance; }\n'
                        '    public String getStatus() { return status; }\n'
                        '}\n'
                    ),
                    "src/main/java/com/tcs/factory/infrastructure/adapter/in/rest/AccountResource.java": (
                        'package com.tcs.factory.infrastructure.adapter.in.rest;\n\n'
                        'import jakarta.ws.rs.*;\n'
                        'import jakarta.ws.rs.core.MediaType;\n'
                        'import jakarta.ws.rs.core.Response;\n'
                        'import java.math.BigDecimal;\n'
                        'import com.tcs.factory.domain.model.Account;\n\n'
                        '@Path("/api/v1/accounts")\n'
                        '@Produces(MediaType.APPLICATION_JSON)\n'
                        '@Consumes(MediaType.APPLICATION_JSON)\n'
                        'public class AccountResource {\n\n'
                        '    @GET\n'
                        '    @Path("/{id}")\n'
                        '    public Response getAccount(@PathParam("id") String id) {\n'
                        '        Account acc = new Account(id, new BigDecimal("1500.00"), "ACTIVE");\n'
                        '        return Response.ok(acc).build();\n'
                        '    }\n'
                        '}\n'
                    )
                }
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # Node 4: Tests generation prompt
        if "TESTS_NODE" in system_prompt:
            output = {
                "files": {
                    "src/test/java/com/tcs/factory/AccountUnitTest.java": (
                        'package com.tcs.factory;\n\n'
                        'import org.junit.jupiter.api.Test;\n'
                        'import static org.junit.jupiter.api.Assertions.*;\n'
                        'import java.math.BigDecimal;\n'
                        'import com.tcs.factory.domain.model.Account;\n\n'
                        'public class AccountUnitTest {\n'
                        '    @Test\n'
                        '    void testAccountCreation() {\n'
                        '        Account acc = new Account("acc-1", new BigDecimal("100"), "ACTIVE");\n'
                        '        assertEquals("acc-1", acc.getId());\n'
                        '    }\n'
                        '}\n'
                    ),
                    "src/test/java/com/tcs/factory/AccountResourceTest.java": (
                        'package com.tcs.factory;\n\n'
                        'import io.quarkus.test.junit.QuarkusTest;\n'
                        'import org.junit.jupiter.api.Test;\n'
                        'import static io.restassured.RestAssured.given;\n'
                        'import static org.hamcrest.CoreMatchers.is;\n\n'
                        '@QuarkusTest\n'
                        'public class AccountResourceTest {\n'
                        '    @Test\n'
                        '    void testGetAccountEndpoint() {\n'
                        '        given()\n'
                        '          .when().get("/api/v1/accounts/acc-123")\n'
                        '          .then()\n'
                        '             .statusCode(200)\n'
                        '             .body("id", is("acc-123"));\n'
                        '    }\n'
                        '}\n'
                    )
                }
            }
            output_str = json.dumps(output, indent=2)
            return output_str, prompt_tokens, len(output_str.split())

        # Default fallback
        fallback = {"status": "ok", "message": "Mock generation executed"}
        fallback_str = json.dumps(fallback)
        return fallback_str, prompt_tokens, len(fallback_str.split())

