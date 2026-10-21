from typing import Any, Dict, Optional, TypedDict


class JobState(TypedDict):
    job_id: str
    user_id: str
    client_code: str
    contract_id: Optional[str]
    requirements: str
    governance_context: Dict[str, Any]
    blueprint: Dict[str, Any]
    files: Dict[str, str]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    duration_ms: int
    status: str
    error: Optional[str]

