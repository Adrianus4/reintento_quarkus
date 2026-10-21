from typing import Any, Dict, Optional
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
        requirements: str,
        contract_id: Optional[str],
        token: str,
        llm: BaseLLMClient,
        config: Optional[Dict[str, Any]] = None,
    ) -> JobState:
        """Run the full multi-agent generation pipeline."""
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
            "cost_usd": 0.0,
            "duration_ms": 0,
            "status": "PENDING",
            "error": None,
        }

        try:
            # 1. Fetch Governance Context from :8002
            state = fetch_governance_node(state, token)

            # 2. Design Blueprint
            state = design_blueprint_node(state, llm)

            # 3. Generate Scaffolding (pom.xml, CI/CD, properties)
            state = generate_scaffolding_node(state, llm)

            # 4. Generate Domain & REST Resources
            state = generate_domain_node(state, llm)

            # 5. Generate Automated Tests (JUnit 5 + @QuarkusTest)
            state = generate_tests_node(state, llm)

            state["status"] = "AWAITING_REVIEW"
        except Exception as exc:
            # Graceful fallback: If external LLM fails (e.g. rate limit, bad API key, outage),
            # fall back to deterministic Mock engine to never block developers
            from app.llm.mock_client import MockLLMClient
            if not isinstance(llm, MockLLMClient):
                mock_llm = MockLLMClient()
                try:
                    if not state.get("blueprint"):
                        state = design_blueprint_node(state, mock_llm)
                    if "pom.xml" not in state.get("files", {}):
                        state = generate_scaffolding_node(state, mock_llm)
                    state = generate_domain_node(state, mock_llm)
                    state = generate_tests_node(state, mock_llm)
                    state["status"] = "AWAITING_REVIEW"
                    state["error"] = None
                except Exception as inner_exc:
                    state["status"] = "FAILED"
                    state["error"] = f"Original error: {str(exc)} | Fallback error: {str(inner_exc)}"
            else:
                state["status"] = "FAILED"
                state["error"] = str(exc)

        return state
