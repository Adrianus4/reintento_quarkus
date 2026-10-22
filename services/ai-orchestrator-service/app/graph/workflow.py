from typing import Any, Dict
from app.graph.nodes import (
    acceptance_tests_node,
    architecture_plan_node,
    fetch_governance_node,
    implement_loop_node,
    repair_agent_node,
    resolve_capabilities_node,
    sandbox_gate_node,
    spec_builder_node,
    spec_lint_and_feasibility_node,
    static_gates_node,
    walking_skeleton_node,
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
        """
        Run TCS Quarkus Factory 2.0 multi-agent generation pipeline:
        fetch_governance -> spec_builder -> spec_lint -> resolve_capabilities ->
        architecture_plan -> acceptance_tests -> walking_skeleton -> implement_loop ->
        static_gates -> sandbox (with Veto Power & Repair Loop)
        """
        state: JobState = {
            "job_id": job_id,
            "user_id": user_id,
            "client_code": client_code,
            "contract_id": contract_id,
            "requirements": requirements,
            "config": config or {},
            "governance_context": {},
            "service_spec": {},
            "spec_hash": "",
            "blueprint": {},
            "capabilities": [],
            "manifest": [],
            "symbol_table": {},
            "files": {},  # Clean dictionary, overwritten on each run
            "static_gate_failures": [],
            "sandbox_result": {},
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

            # 2. Spec Builder (Universal ServiceSpec generation)
            state = spec_builder_node(state, llm)

            # 3. Spec Lint & Feasibility Check (Early Failure if unfeasible)
            state = spec_lint_and_feasibility_node(state)
            if state.get("status") == "FAILED":
                return state

            # 4. Resolve Capabilities & Scaffolding (Deterministic POM & properties from Catalog)
            state = resolve_capabilities_node(state)

            # 5. Architectural Plan (Manifest & Symbol Table)
            state = architecture_plan_node(state)

            # 6. Acceptance Tests (Immutable Test Oracle)
            state = acceptance_tests_node(state, llm)

            # 7. Walking Skeleton (Compilable interfaces, DTOs & Stubs)
            state = walking_skeleton_node(state)

            # 8. Implement Loop
            state = implement_loop_node(state, llm)

            # 9. Static Gates (AST syntax, package prefix, symbol resolution, no secrets)
            state = static_gates_node(state)
            if state.get("static_gate_failures"):
                state = repair_agent_node(state, llm)
                state = static_gates_node(state)
                if state.get("static_gate_failures"):
                    state["status"] = "FAILED"
                    return state

            # 10. Ephemeral Sandbox with Strict Veto Power & Auto-Repair Loop
            max_repair_attempts = 4
            for attempt in range(max_repair_attempts):
                state = sandbox_gate_node(state, token)
                if state.get("status") == "VERIFIED_PASSED":
                    break
                if state.get("status") == "VERIFICATION_UNAVAILABLE" or attempt == max_repair_attempts - 1:
                    break
                state = repair_agent_node(state, llm)
                state = static_gates_node(state)
                if state.get("static_gate_failures"):
                    break

            # Final status update
            if state.get("status") == "VERIFIED_PASSED":
                state["status"] = "AWAITING_REVIEW"
            else:
                state["status"] = "FAILED"
                state["error"] = state.get("error") or "Project has not passed verification."

        except Exception as exc:
            import traceback
            traceback.print_exc()
            state["status"] = "FAILED"
            state["error"] = f"Pipeline execution error: {str(exc)}"

        return state
