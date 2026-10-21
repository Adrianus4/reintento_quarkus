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
    cfg = state.get("config", {})
    client_ctx = state.get("governance_context", {}).get("client", {})
    default_pkg = client_ctx.get("package_prefix", f"pe.com.{state['client_code']}")

    system_prompt = (
        "BLUEPRINT_DESIGN_NODE: You are an enterprise Java and Quarkus Software Architect at Tata Consultancy Services (TCS). "
        "Analyze the requirements, OpenAPI contract, and client governance guidelines. "
        "ARCHITECTURAL RULES:\n"
        "1. NO ONE-SIZE-FITS-ALL: Respect the user's selected architecture, security, database, and extensions choices.\n"
        "2. STRICTLY ENFORCE MANDATORY DIRECTIVES: Enforce mandatory policies (Java 17/21, Quarkus Core, ArC CDI, RESTEasy Reactive, Quarkus Security, JUnit 5 / @QuarkusTest).\n"
        "3. ZERO OVER-ENGINEERING & 100% STATELESS: If the user selects NO database ('NONE' or stateless), you MUST NOT include Hibernate, Panache, JDBC, or any persistence libraries. The microservice must be strictly 100% stateless.\n"
        "4. DETERMINISTIC VALIDATION: Ensure all package prefixes and dependency coordinates conform to client governance.\n"
        "5. ZERO ERRORS IN QUARKUS: The generated project must be free of syntax, dependency, or compilation errors.\n"
        "Output ONLY a valid JSON object defining: architecture_style, quarkus_version, java_version, "
        "package_prefix, dependencies (list), entities (list), endpoints (list)."
    )
    user_prompt = (
        f"Client Code: {state['client_code']}\n"
        f"Requirements: {state['requirements']}\n"
        f"User Architecture Selection: {cfg.get('architecture_style', 'Hexagonal')}\n"
        f"User Architecture Notes: {cfg.get('custom_architecture_notes')}\n"
        f"User Security Selection: {cfg.get('security_option', 'JWT')}\n"
        f"User Security Roles: {json.dumps(cfg.get('security_roles', []))}\n"
        f"User Communication Protocol: {cfg.get('communication_protocol', 'REST')}\n"
        f"User Custom Endpoints: {json.dumps(cfg.get('custom_endpoints', []))}\n"
        f"User Database Selection: {cfg.get('database_option', 'POSTGRESQL_PANACHE')}\n"
        f"User Database Name: {cfg.get('database_name')}\n"
        f"User Package Prefix: {cfg.get('package_prefix') or default_pkg}\n"
        f"User Artifact ID: {cfg.get('artifact_id')}\n"
        f"User HTTP Port: {cfg.get('http_port', 8080)}\n"
        f"User Requested Extensions: {json.dumps(cfg.get('extensions', []))}\n"
        f"User Custom Free Extensions: {json.dumps(cfg.get('custom_extensions', []))}\n"
        f"User Custom Properties: {json.dumps(cfg.get('custom_properties', {}))}\n"
        f"User Defined Entities: {json.dumps(cfg.get('entities', []))}\n"
        f"Governance: {json.dumps(state['governance_context'])}\n"
    )

    t0 = time.time()
    text, p_tok, c_tok = llm.generate(system_prompt, user_prompt)
    state["duration_ms"] += int((time.time() - t0) * 1000)
    state["prompt_tokens"] += p_tok
    state["completion_tokens"] += c_tok

    parsed = extract_and_parse_json(text)
    if not isinstance(parsed, dict):
        parsed = {}

    # Override or ensure user explicit selections take precedence
    if cfg.get("architecture_style"):
        raw_arch = cfg["architecture_style"]
        if "hex" in raw_arch.lower():
            parsed["architecture_style"] = "Hexagonal"
        elif "layer" in raw_arch.lower():
            parsed["architecture_style"] = "Layered"
        elif "event" in raw_arch.lower():
            parsed["architecture_style"] = "Event-Driven"
        else:
            parsed["architecture_style"] = raw_arch.capitalize()
    if cfg.get("package_prefix"):
        parsed["package_prefix"] = cfg["package_prefix"]
    elif not parsed.get("package_prefix"):
        parsed["package_prefix"] = default_pkg
    if cfg.get("java_version"):
        parsed["java_version"] = cfg["java_version"]
    if cfg.get("entities") and len(cfg["entities"]) > 0:
        parsed["entities"] = cfg["entities"]
    if cfg.get("security_option"):
        parsed["security_option"] = cfg["security_option"]
    if cfg.get("database_option"):
        parsed["database_option"] = cfg["database_option"]
    if cfg.get("extensions"):
        parsed["user_extensions"] = cfg["extensions"]

    state["blueprint"] = parsed
    state["status"] = "BLUEPRINT_DESIGNED"
    return state


def generate_scaffolding_node(state: JobState, llm: BaseLLMClient) -> JobState:
    """AI agent generates pom.xml, application.properties, and CI/CD workflow."""
    system_prompt = (
        "SCAFFOLDING_NODE: You are an enterprise DevSecOps and Java Scaffolding Engineer at Tata Consultancy Services (TCS). "
        "Generate pom.xml with Quarkus 3.x BOM and strictly requested dependencies (if stateless with no database, strictly ZERO Hibernate, Panache, or JDBC dependencies), "
        "application.properties (with zero hardcoded secrets; using environment variable placeholders), "
        "and .github/workflows/ci.yml with automated deterministic verification in Docker/Maven ('mvn -B clean test'). "
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

