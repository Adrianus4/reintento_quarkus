from typing import Any, Dict, List, Optional, TypedDict


class JobState(TypedDict, total=False):
    job_id: str
    user_id: str
    client_code: str
    contract_id: Optional[str]
    requirements: str
    config: Dict[str, Any]
    governance_context: Dict[str, Any]
    blueprint: Dict[str, Any]
    files: Dict[str, str]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    duration_ms: int
    status: str
    error: Optional[str]
