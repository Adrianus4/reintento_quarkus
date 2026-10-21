# Phase 0 Research: Spec 003 — ai-orchestrator-service

## 1. Technical Decisions & Trade-Offs

### 1.1 Architecture & Boundaries
- **Decision**: Dedicated microservice in FastAPI running on port `8003`.
- **Rationale**: Isolates AI model communication, token costs, prompt engineering, and stateful LangGraph workflows from auth, governance, and the physical compilation sandbox.
- **Port**: `8003`
- **Swagger Documentation**: `http://localhost:8003/docs`

### 1.2 Encrypted Credential Vault (Fernet)
- **Decision**: Symmetric encryption in reposo using `cryptography.fernet.Fernet` with a master key (`VAULT_MASTER_KEY`).
- **Safety Rules**:
  - API keys are encrypted immediately upon reception.
  - Plaintext is only kept in memory during transient LLM API calls.
  - Endpoints returning vault keys only expose `masked_key` (e.g. `AIza...98a`).
  - Strict ADMIN authorization required for any vault modification.

### 1.3 LLM Multi-Provider Gateway & Hot Conmutation
- **Supported Providers**:
  - **Google Gemini**: Gemini 2.5 Flash, Gemini 2.5 Pro.
  - **DeepSeek**: DeepSeek Chat, DeepSeek Reasoner (OpenAI-compatible format).
  - **Grok**: Grok 2, Grok 2 mini (xAI OpenAI-compatible format).
  - **Mock / Offline Engine**: Deterministic mock provider that produces complete, valid Quarkus Java projects for instant hermetic unit tests with zero network latency.
- **Consumption Modes**:
  - `economic`: Minimum token overhead, rapid responses.
  - `balanced`: Default recommended mode for production microservice generation.
  - `advanced`: Maximum reasoning depth for complex business logic.
- **Hot-Switching**: Dynamic gateway configuration stored in memory/DB without requiring process restart.

### 1.4 Resilient JSON Parser & Repair
- **Problem**: Large generation prompts can produce markdown code fences, trailing commas, or truncated output if token limits are reached.
- **Solution**:
  - Guarantee `maxOutputTokens >= 8192`.
  - Regex extraction for ````json ... ```` blocks.
  - Automatic dangling quote, bracket, and brace closure parser before deserialization.

### 1.5 LangGraph Multi-Agent Architecture
- **State Machine**:
  ```text
  [Start] 
     ↓
  (fetch_governance) → Fetches client guidelines & OpenAPI contract from :8002
     ↓
  (design_blueprint) → Determines Architecture (Hexagonal, Layered, etc.) & BOM
     ↓
  (generate_scaffolding) → Builds pom.xml, application.properties, CI/CD
     ↓
  (generate_domain) → Generates models, DTOs, services, controllers
     ↓
  (generate_tests) → Generates JUnit 5 and @QuarkusTest RestAssured tests
     ↓
  (await_review) → State: AWAITING_REVIEW (Human-in-the-Loop)
     ↓
  [Human Approval via POST /approve] → State: APPROVED (Ready for Sandbox :8004)
  ```
- **Budget Tracking**:
  - Accumulates prompt and completion tokens.
  - Calculates estimated cost in USD based on provider price matrix.
  - Tracks execution duration in milliseconds.

---

## 2. Directory Layout Decision

```text
services/ai-orchestrator-service/
├── app/
│   ├── api/
│   │   ├── deps.py               # Auth & client access verification
│   │   └── v1/
│   │       ├── api.py            # Central router
│   │       ├── vault.py          # /vault (Encrypted credentials CRUD & connection test)
│   │       ├── gateway.py        # /ai-gateway (Provider config & mode selection)
│   │       └── orchestrator.py   # /orchestrator/jobs (LangGraph jobs, editing & approval)
│   ├── core/
│   │   ├── config.py             # Port 8003, VAULT_MASTER_KEY, DB_URL
│   │   ├── database.py           # SQLAlchemy 2.0
│   │   ├── vault.py              # Fernet encryption/decryption engine
│   │   └── parser.py             # Resilient JSON repair utility
│   ├── models/
│   │   ├── credential.py         # VaultCredential model
│   │   ├── gateway_config.py     # GatewayConfig model
│   │   └── job.py                # GenerationJob model
│   ├── schemas/
│   │   ├── vault.py              # VaultKeySaveRequest, VaultKeyResponse
│   │   ├── gateway.py            # GatewayConfigUpdate, GatewayConfigResponse
│   │   └── job.py                # JobCreateRequest, JobResponse, FileEditRequest
│   ├── llm/
│   │   ├── base.py               # BaseLLMClient interface
│   │   ├── factory.py            # LLMClientFactory with hot switching
│   │   ├── mock_client.py        # Deterministic offline mock client
│   │   ├── gemini_client.py      # Google Gemini client
│   │   └── openai_compat.py      # DeepSeek and Grok client
│   ├── graph/
│   │   ├── state.py              # JobState TypedDict
│   │   ├── nodes.py              # LangGraph workflow nodes
│   │   └── workflow.py           # Compiled LangGraph pipeline
│   └── main.py                   # FastAPI app entrypoint
├── tests/
│   ├── conftest.py               # Test fixtures & mock tokens
│   ├── test_vault.py             # Fernet encryption & credentials tests
│   ├── test_gateway.py           # Hot-switching & provider config tests
│   ├── test_parser.py            # Resilient JSON repair tests
│   └── test_orchestrator.py      # LangGraph generation, editing, and approval tests
├── requirements.txt
├── Dockerfile
└── README.md
```

