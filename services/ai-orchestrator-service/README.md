# TCS Intelligent Microservice Factory — AI Orchestrator Service

Microservice dedicated to encrypted credential governance, multi-provider AI gateway (Gemini, DeepSeek, Grok, Mock), and stateful LangGraph multi-agent generation workflows.

- **Port**: `8003`
- **Swagger Documentation**: `http://localhost:8003/docs`
- **Constitution Version**: `1.2.0`

## Features

1. **Fernet Credential Vault**: Stores provider API keys encrypted at rest. Never exposes keys in plain text.
2. **AI Gateway Hot-Switching**: Dynamically switch active provider (`gemini`, `deepseek`, `grok`, `mock`) and consumption modes (`economic`, `balanced`, `advanced`) on the fly.
3. **Resilient JSON Parser**: Tolerates markdown code fences and auto-repairs truncated quotes, brackets, and braces.
4. **LangGraph Multi-Agent Pipeline**: Sequentially designs blueprints (Hexagonal, Layered, etc.), scaffolds `pom.xml` and CI/CD, generates domain models and REST endpoints, and builds automated tests (`JUnit 5` + `@QuarkusTest`).
5. **Human-in-the-Loop**: Developers inspect generated code, edit files in place, and approve the microservice prior to sandbox compilation.

## Quickstart

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

## Running Tests

```bash
pytest -v
```

