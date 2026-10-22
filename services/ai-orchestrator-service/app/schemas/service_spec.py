"""
Universal Service Specification (ServiceSpec) Model for TCS Quarkus Factory.
Replaces simplistic entity-only blueprints with full behavioral microservice specifications.
Supports all architectures: REST, Kafka, AMQP, Batch, Sagas, Calculators, Legacy SOAP, gRPC, etc.
"""

from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class InboundKind(str, Enum):
    REST = "rest"
    GRPC = "grpc"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    KAFKA_CONSUMER = "kafka_consumer"
    AMQP_CONSUMER = "amqp_consumer"
    SCHEDULER = "scheduler"
    FILE_WATCHER = "file_watcher"
    BATCH_JOB = "batch_job"
    WEBHOOK = "webhook"
    CLI = "cli"


class OutboundKind(str, Enum):
    DATABASE = "database"
    REST_CLIENT = "rest_client"
    SOAP_CLIENT = "soap_client"
    GRPC_CLIENT = "grpc_client"
    KAFKA_PRODUCER = "kafka_producer"
    AMQP_PRODUCER = "amqp_producer"
    CACHE = "cache"
    OBJECT_STORAGE = "object_storage"
    EMAIL = "email"
    SMS = "sms"
    LLM = "llm"
    FTP = "ftp"
    LEGACY = "legacy"


class DomainComponentKind(str, Enum):
    CALCULATOR = "calculator"
    VALIDATOR = "validator"
    STATE_MACHINE = "state_machine"
    ORCHESTRATOR = "orchestrator"
    SAGA = "saga"
    TRANSFORMER = "transformer"
    AGGREGATOR = "aggregator"
    ROUTER = "router"
    POLICY = "policy"
    SERVICE = "service"


class ServiceMetadata(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    purpose: str = Field(..., min_length=5)
    archetype_hint: Optional[str] = "hexagonal"


class InboundDeclaration(BaseModel):
    id: str = Field(..., description="Unique inbound identifier, e.g. 'rest-campaign-customers' or 'kafka-orders-in'")
    kind: InboundKind
    contract_ref: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="e.g. path, http_method, topic, cron, port")


class OutboundDeclaration(BaseModel):
    id: str = Field(..., description="Unique outbound identifier, e.g. 'db-postgres' or 'kafka-events-out'")
    kind: OutboundKind
    contract_ref: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict, description="e.g. db_type, topic, client_url, queue")


class DataField(BaseModel):
    name: str
    type: str = "String"
    required: bool = True
    is_id: bool = False
    validation_regex: Optional[str] = None
    description: Optional[str] = None


class DataModel(BaseModel):
    name: str
    table_name: Optional[str] = None
    fields: List[DataField] = Field(default_factory=list)


class DomainComponent(BaseModel):
    id: str
    kind: DomainComponentKind
    description: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)


class StateTransition(BaseModel):
    from_state: str
    to_state: str
    trigger: str
    action: Optional[str] = None


class StateMachineSpec(BaseModel):
    id: str
    states: List[str]
    initial_state: str
    terminal_states: List[str] = Field(default_factory=list)
    transitions: List[StateTransition] = Field(default_factory=list)


class SagaStep(BaseModel):
    step_id: str
    action: str
    outbound_ref: str
    compensation_action: str
    compensation_outbound_ref: Optional[str] = None


class SagaWorkflow(BaseModel):
    id: str
    name: str
    steps: List[SagaStep]


class DomainSpec(BaseModel):
    data_models: List[DataModel] = Field(default_factory=list)
    components: List[DomainComponent] = Field(default_factory=list)
    state_machines: List[StateMachineSpec] = Field(default_factory=list)
    workflows: List[SagaWorkflow] = Field(default_factory=list)


class BehaviorExample(BaseModel):
    input: Dict[str, Any]
    expected_output: Dict[str, Any]


class BehaviorSpec(BaseModel):
    id: str
    given: str = Field(..., description="Preconditions or initial state")
    when: str = Field(..., description="Inbound trigger, e.g. 'POST /api/v1/customers with valid JSON'")
    inbound_ref: str = Field(..., description="Reference to InboundDeclaration.id")
    then: str = Field(..., description="Observable outcome on outbound, response, or state")
    outbound_ref: Optional[str] = Field(None, description="Reference to OutboundDeclaration.id")
    examples: List[BehaviorExample] = Field(default_factory=list)


class NonFunctionalSpec(BaseModel):
    security: Dict[str, Any] = Field(default_factory=lambda: {"auth_type": "JWT", "roles": ["ADMIN", "OPERATOR"]})
    resilience: Dict[str, Any] = Field(default_factory=lambda: {"timeout_ms": 3000, "circuit_breaker": True, "retry": 2})
    idempotency: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True, "header": "X-Idempotency-Key"})
    observability: Dict[str, Any] = Field(default_factory=lambda: {"health_check": True, "metrics": True, "tracing": True})
    consistency: str = "strong"  # "strong" | "eventual"


class GovernanceRef(BaseModel):
    client_code: str
    package_prefix: str
    java_version: str = "21"
    quarkus_version: str = "3.15.1"


class ServiceSpec(BaseModel):
    version: str = "2.0"
    service: ServiceMetadata
    inbound: List[InboundDeclaration] = Field(default_factory=list)
    outbound: List[OutboundDeclaration] = Field(default_factory=list)
    domain: DomainSpec = Field(default_factory=DomainSpec)
    behaviors: List[BehaviorSpec] = Field(..., min_length=1, description="At least one behavior is MANDATORY")
    non_functional: NonFunctionalSpec = Field(default_factory=NonFunctionalSpec)
    governance_ref: GovernanceRef

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash to freeze specification before build."""
        spec_dict = self.model_dump(mode="json")
        canonical_json = json.dumps(spec_dict, sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

