# TCS Intelligent Microservice Factory — Sandbox Verifier Service

Microservice dedicated to ephemeral workspace execution, Maven compilation, Surefire test runs, SHA-256 verification manifest generation, and ZIP packaging.

- **Port**: `8004`
- **Swagger Documentation**: `http://localhost:8004/docs`
- **Constitution Version**: `1.2.0`

## Features

1. **Ephemeral Sandboxing**: Safely materializes generated projects into isolated runs with strict path traversal defenses.
2. **Compilation Engine**: Executes native Maven (`mvn -B clean test-compile`) or resilient deterministic Java/Quarkus syntax validation.
3. **Cryptographic Manifest**: Calculates SHA-256 hashes for all source files, generating `VERIFICATION_MANIFEST.json` per Constitution Principle XIV.
4. **ZIP Packaging & Download**: Packages the microservice into a clean `.zip` archive for immediate developer download.

## Quickstart

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8004 --reload
```

## Running Tests

```bash
pytest -v
```

