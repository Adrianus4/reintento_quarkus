"""
scripts/start_factory.py
TCS Intelligent Microservice Factory -- Cluster Launcher in Python
Runs cross-platform without PowerShell ExecutionPolicy limitations.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SERVICES = [
    {
        "name": "auth-access-service",
        "port": 8001,
        "path": BASE_DIR / "services" / "auth-access-service",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
    },
    {
        "name": "client-governance-service",
        "port": 8002,
        "path": BASE_DIR / "services" / "client-governance-service",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
    },
    {
        "name": "ai-orchestrator-service",
        "port": 8003,
        "path": BASE_DIR / "services" / "ai-orchestrator-service",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
    },
    {
        "name": "sandbox-verifier-service",
        "port": 8004,
        "path": BASE_DIR / "services" / "sandbox-verifier-service",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
    },
]

def main():
    print("=" * 64)
    print("   TATA CONSULTANCY SERVICES (TCS)")
    print("   Intelligent Microservice Factory -- Multi-Agent Cluster")
    print("=" * 64)
    print()

    headless = "--headless" in sys.argv or "--background" in sys.argv or "--no-window" in sys.argv
    logs_dir = BASE_DIR / ".logs"
    if headless:
        logs_dir.mkdir(exist_ok=True)
        print(f"[*] Modo headless activado. Logs en: {logs_dir}")

    processes = []
    log_files = []

    print("[1/2] Iniciando los 4 microservicios backend...")
    for svc in SERVICES:
        print(f"  -> Levantando {svc['name']} en puerto {svc['port']}...")
        if headless:
            log_file = (logs_dir / f"{svc['name']}.log").open("a", encoding="utf-8")
            log_files.append(log_file)
            p = subprocess.Popen(
                svc["cmd"],
                cwd=str(svc["path"]),
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
        elif os.name == "nt":
            # On Windows, spawn in a separate console window so logs can be inspected
            p = subprocess.Popen(
                svc["cmd"],
                cwd=str(svc["path"]),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            p = subprocess.Popen(svc["cmd"], cwd=str(svc["path"]))
        processes.append((svc["name"], p))
        time.sleep(0.5)

    print()
    print("[2/2] Iniciando el Frontend Workspace Studio (tcs-factory-ui)...")
    ui_path = BASE_DIR / "services" / "tcs-factory-ui"
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    if headless:
        ui_log = (logs_dir / "tcs-factory-ui.log").open("a", encoding="utf-8")
        log_files.append(ui_log)
        ui_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(ui_path),
            stdout=ui_log,
            stderr=subprocess.STDOUT
        )
    elif os.name == "nt":
        ui_proc = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(ui_path),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        ui_proc = subprocess.Popen([npm_cmd, "run", "dev"], cwd=str(ui_path))
    processes.append(("tcs-factory-ui", ui_proc))

    time.sleep(1)

    print()
    print("=" * 64)
    print("   CLÚSTER INICIADO CORRECTAMENTE:")
    print("=" * 64)
    print("  - UI Workspace Studio:      http://localhost:5173")
    print("  - Auth Access Service:       http://localhost:8001/api/v1/health")
    print("  - Client Governance Service: http://localhost:8002/api/v1/health")
    print("  - AI Orchestrator Service:   http://localhost:8003/api/v1/health")
    print("  - Sandbox Verifier Service:  http://localhost:8004/api/v1/health")
    print("=" * 64)
    print()
    print("Presiona Ctrl+C en esta consola o cierra las ventanas de terminal para detener.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo clúster...")
        for name, proc in processes:
            proc.terminate()
        for f in log_files:
            try:
                f.close()
            except Exception:
                pass
        print("Clúster detenido.")

if __name__ == "__main__":
    main()

