from typing import Any, Dict, List, Optional, TypedDict


class FileManifestEntry(TypedDict, total=False):
    path: str
    fqcn: Optional[str]
    origin: str  # "template" | "llm" | "scaffold"
    public_signatures: List[str]
    dependencies: List[str]
    layer: Optional[str]


class StaticGateFailure(TypedDict, total=False):
    gate: str
    file: Optional[str]
    line: Optional[int]
    message: str


class JobState(TypedDict, total=False):
    job_id: str
    user_id: str
    client_code: str
    contract_id: Optional[str]
    requirements: str
    config: Dict[str, Any]
    governance_context: Dict[str, Any]
    service_spec: Dict[str, Any]         # Universal ServiceSpec model
    spec_hash: str                      # SHA-256 frozen spec hash
    blueprint: Dict[str, Any]           # Kept for backward compatibility
    capabilities: List[str]             # Resolved capabilities from catalog
    manifest: List[FileManifestEntry]   # Architectural plan manifest (immutable contract)
    symbol_table: Dict[str, List[str]]  # FQCN -> exported public methods/symbols
    files: Dict[str, str]               # Clean dictionary of relative_path -> content (overwritten clean)
    static_gate_failures: List[StaticGateFailure]
    sandbox_result: Dict[str, Any]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    duration_ms: int
    status: str
    error: Optional[str]
