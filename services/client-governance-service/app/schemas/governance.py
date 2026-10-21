from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas.client import ClientResponse
from app.schemas.contract import ContractResponse
from app.schemas.directive import DirectiveResponse


class GovernanceContextResponse(BaseModel):
    client: ClientResponse
    mandatory_directives: List[DirectiveResponse]
    recommended_directives: List[DirectiveResponse]
    optional_directives: List[DirectiveResponse]
    contract: Optional[ContractResponse] = None
    metadata: Dict[str, Any] = {}

