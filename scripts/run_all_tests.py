import os
import subprocess
import sys
from pathlib import Path

SERVICES = [
    "services/auth-access-service",
    "services/client-governance-service",
    "services/ai-orchestrator-service",
    "services/sandbox-verifier-service",
]


def run_tests():
    root_dir = Path(__file__).resolve().parent.parent
    all_passed = True
    results = {}

    print("=================================================================")
    print(" TCS Intelligent Microservice Factory -- Multi-Service Test Runner ")
    print("=================================================================\n")

    for service_rel in SERVICES:
        service_dir = root_dir / service_rel
        if not service_dir.exists():
            print(f"[-] Skipping {service_rel} (Directory not found)")
            continue

        print(f"[>] Running tests for: {service_rel}...")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(service_dir)

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-v"],
            cwd=str(service_dir),
            env=env,
            capture_output=True,
            text=True
        )

        passed = (proc.returncode == 0)
        results[service_rel] = {
            "passed": passed,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

        if passed:
            print(f"[PASS] {service_rel}")
        else:
            print(f"[FAIL] {service_rel}")
            print(proc.stdout)
            print(proc.stderr)
            all_passed = False

    print("\n-----------------------------------------------------------------")
    print("Summary:")
    for s, res in results.items():
        status = "PASSED" if res["passed"] else "FAILED"
        print(f" - {s}: {status}")
    print("-----------------------------------------------------------------")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    run_tests()
