import json
import time
from typing import Any, Dict
import httpx
from app.core.config import settings
from app.core.parser import extract_and_parse_json
from app.graph.state import JobState
from app.llm.base import BaseLLMClient


def fetch_governance_node(state: JobState, token: str) -> JobState:
    """Fetch client profile, directives, and OpenAPI contract from client-governance-service."""
    client_code = state["client_code"]
    contract_id = state.get("contract_id")

    url = f"{settings.GOVERNANCE_SERVICE_URL}/clients/{client_code}/governance-context"
    params = {}
    if contract_id:
        params["contract_id"] = contract_id

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                state["governance_context"] = resp.json()
            else:
                state["governance_context"] = {
                    "client": {
                        "code": client_code,
                        "name": client_code.upper(),
                        "package_prefix": f"com.tcs.{client_code}",
                        "java_version": "17",
                        "quarkus_version": "3.15.1"
                    },
                    "mandatory_directives": [],
                    "recommended_directives": [],
                    "optional_directives": []
                }
    except Exception:
        state["governance_context"] = {
            "client": {
                "code": client_code,
                "name": client_code.upper(),
                "package_prefix": f"com.tcs.{client_code}",
                "java_version": "17",
                "quarkus_version": "3.15.1"
            },
            "mandatory_directives": [],
            "recommended_directives": [],
            "optional_directives": []
        }

    return state


def design_blueprint_node(state: JobState, llm: BaseLLMClient) -> JobState:
    """AI agent designs the architectural blueprint (Adaptive style: Hexagonal, Layered, etc.)."""
    system_prompt = (
        "BLUEPRINT_DESIGN_NODE: You are an enterprise Java and Quarkus Software Architect at Tata Consultancy Services (TCS). "
        "Analyze the requirements, OpenAPI contract, and client governance guidelines. "
        "ARCHITECTURAL RULES:\n"
        "1. NO ONE-SIZE-FITS-ALL: Do NOT incorporate all technologies automatically. Select only pertinent technologies justified by the functional and non-functional requirements.\n"
        "2. STRICTLY ENFORCE MANDATORY DIRECTIVES: Enforce mandatory policies (Java 17/21, Quarkus Core, ArC CDI, RESTEasy Reactive, Quarkus Security JWT, JUnit 5 / @QuarkusTest / REST-assured, Panache SQL Server).\n"
        "3. ON-DEMAND OPTIONAL TECHNOLOGIES: Incorporate reactive events (SmallRye Reactive Messaging / Kafka / Azure Service Bus) or NoSQL (MongoDB / Cosmos DB) ONLY when explicitly required by the use case.\n"
        "4. DETERMINISTIC VALIDATION: Ensure all package prefixes and dependency coordinates conform to client governance.\n"
        "Output ONLY a valid JSON object defining: architecture_style, quarkus_version, java_version, "
        "package_prefix, dependencies (list), entities (list), endpoints (list)."
    )
    user_prompt = (
        f"Client Code: {state['client_code']}\n"
        f"Requirements: {state['requirements']}\n"
        f"Governance: {json.dumps(state['governance_context'])}\n"
    )

    t0 = time.time()
    text, p_tok, c_tok = llm.generate(system_prompt, user_prompt)
    state["duration_ms"] += int((time.time() - t0) * 1000)
    state["prompt_tokens"] += p_tok
    state["completion_tokens"] += c_tok

    parsed = extract_and_parse_json(text)
    state["blueprint"] = parsed
    state["status"] = "BLUEPRINT_DESIGNED"
    return state


def generate_scaffolding_node(state: JobState, llm: BaseLLMClient) -> JobState:
    """AI agent generates pom.xml, application.properties, and CI/CD workflow."""
    system_prompt = (
        "SCAFFOLDING_NODE: You are an enterprise DevSecOps and Java Scaffolding Engineer at Tata Consultancy Services (TCS). "
        "Generate pom.xml with Quarkus 3.x BOM and strictly allowed client dependencies, "
        "application.properties (with zero hardcoded secrets; using environment variable placeholders), "
        "and .github/workflows/ci.yml with automated deterministic verification ('mvn -B clean test'). "
        "Output ONLY a JSON object with a 'files' map containing relative file paths as keys and file contents as values."
    )
    user_prompt = (
        f"Blueprint: {json.dumps(state['blueprint'])}\n"
        f"Governance: {json.dumps(state['governance_context'])}\n"
    )

    t0 = time.time()
    text, p_tok, c_tok = llm.generate(system_prompt, user_prompt)
    state["duration_ms"] += int((time.time() - t0) * 1000)
    state["prompt_tokens"] += p_tok
    state["completion_tokens"] += c_tok

    parsed = extract_and_parse_json(text)
    new_files = parsed.get("files", {})
    state["files"].update(new_files)
    state["status"] = "SCAFFOLDED"
    return state


def generate_domain_node(state: JobState, llm: BaseLLMClient) -> JobState:
    """AI agent generates domain models, ports/interfaces, and REST resources."""
    system_prompt = (
        "DOMAIN_CODE_NODE: You are a Senior Java and Quarkus Developer. "
        "Implement clean domain models, DTOs, and REST resources following the blueprint architecture. "
        "Output ONLY a JSON object with a 'files' map containing relative file paths and complete Java code."
    )
    user_prompt = (
        f"Blueprint: {json.dumps(state['blueprint'])}\n"
        f"Requirements: {state['requirements']}\n"
    )

    t0 = time.time()
    text, p_tok, c_tok = llm.generate(system_prompt, user_prompt)
    state["duration_ms"] += int((time.time() - t0) * 1000)
    state["prompt_tokens"] += p_tok
    state["completion_tokens"] += c_tok

    parsed = extract_and_parse_json(text)
    new_files = parsed.get("files", {})
    state["files"].update(new_files)
    state["status"] = "DOMAIN_GENERATED"
    return state


def generate_tests_node(state: JobState, llm: BaseLLMClient) -> JobState:
    """AI agent generates JUnit 5 unit tests and @QuarkusTest API tests."""
    system_prompt = (
        "TESTS_NODE: You are an enterprise QA and Automation Engineer. "
        "Generate automated tests using JUnit 5 and @QuarkusTest with REST-assured. "
        "Output ONLY a JSON object with a 'files' map containing test files."
    )
    user_prompt = (
        f"Blueprint: {json.dumps(state['blueprint'])}\n"
        f"Existing Files: {list(state['files'].keys())}\n"
    )

    t0 = time.time()
    text, p_tok, c_tok = llm.generate(system_prompt, user_prompt)
    state["duration_ms"] += int((time.time() - t0) * 1000)
    state["prompt_tokens"] += p_tok
    state["completion_tokens"] += c_tok

    parsed = extract_and_parse_json(text)
    new_files = parsed.get("files", {})
    state["files"].update(new_files)

    # Estimate cost ($0.30 per 1M prompt tokens, $1.20 per 1M completion tokens standard rate)
    cost = (state["prompt_tokens"] * 0.00000030) + (state["completion_tokens"] * 0.00000120)
    state["cost_usd"] = round(cost, 6)

    state["status"] = "AWAITING_REVIEW"
    return state

