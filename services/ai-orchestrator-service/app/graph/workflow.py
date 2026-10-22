import json
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.graph.nodes import (
    design_blueprint_node,
    fetch_governance_node,
    generate_domain_node,
    generate_scaffolding_node,
    generate_tests_node,
)
from app.graph.state import JobState
from app.llm.base import BaseLLMClient


class GenerationWorkflow:
    @staticmethod
    def run_pipeline(
        job_id: str,
        user_id: str,
        client_code: str,
        contract_id: str = None,
        requirements: str = "",
        config: Dict[str, Any] = None,
        llm: BaseLLMClient = None,
        token: str = None
    ) -> JobState:
        """Run sequential LangGraph execution pipeline."""
        state: JobState = {
            "job_id": job_id,
            "user_id": user_id,
            "client_code": client_code,
            "contract_id": contract_id,
            "requirements": requirements,
            "config": config or {},
            "governance_context": {},
            "blueprint": {},
            "files": {},
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "duration_ms": 0,
            "cost_usd": 0.0,
            "status": "PENDING",
            "error": None,
        }

        try:
            # 1. Fetch Governance Context from :8002
            state = fetch_governance_node(state, token)

            # 2. Design Blueprint
            state = design_blueprint_node(state, llm)

            # 3. Generate Scaffolding (pom.xml or build.gradle, CI/CD, properties)
            state = generate_scaffolding_node(state, llm)

            # 4. Generate Domain & REST Resources
            state = generate_domain_node(state, llm)

            # 5. Generate Automated Tests (JUnit 5 + @QuarkusTest)
            state = generate_tests_node(state, llm)

            state["status"] = "AWAITING_REVIEW"
        except Exception as exc:
            # Report the actual error from the configured LLM without silent mock fallbacks
            state["status"] = "FAILED"
            state["error"] = f"Error invocando el modelo {getattr(llm, 'model_name', 'LLM')}: {str(exc)}"

        return state
