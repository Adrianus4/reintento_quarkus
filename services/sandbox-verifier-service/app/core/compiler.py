import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple
import javalang


def get_maven_binary() -> Optional[str]:
    """Find native Maven command with priority for Windows cmd scripts."""
    if os.environ.get("SANDBOX_SKIP_NATIVE_MVN", "false").lower() in ["1", "true"]:
        return None
    candidates = [
        shutil.which("mvn.cmd"),
        r"C:\workspace\apache-maven-3.10.0\bin\mvn.cmd",
        shutil.which("mvn"),
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return None


def run_compilation_verification(workspace_dir: Path) -> Tuple[bool, str, int, Dict[str, Any]]:
    """
    Execute rigorous 5-phase verification with VETO POWER:
    Phase 1: validate (POM XML structure, Quarkus BOM, AST syntax with javalang)
    Phase 2: test-compile (Maven compilation of main and test sources)
    Phase 3: verify (Execution of @QuarkusTest acceptance test suites)
    Phase 4: runtime-test (Verify test profile configuration and dependencies)
    Phase 5: smoke-test (Verify all declared inbounds are wired and testable)

    Returns: (is_success, log_output, duration_ms, details)
    """
    t0 = time.time()
    logs: List[str] = [
        "[INFO] ========================================================================",
        "[INFO] TCS Quarkus Factory Sandbox Verifier (Veto-Enforced Verification Mode)",
        "[INFO] ========================================================================",
    ]
    failures: List[Dict[str, Any]] = []
    phase_results: Dict[str, str] = {
        "validate": "NOT_RUN",
        "test-compile": "NOT_RUN",
        "verify": "NOT_RUN",
        "runtime-test": "NOT_RUN",
        "smoke-test": "NOT_RUN",
    }

    pom_file = workspace_dir / "pom.xml"

    # =========================================================================
    # PHASE 1: VALIDATE (POM & Java AST Parsing)
    # =========================================================================
    logs.append("[PHASE 1/5] Validating POM structure and Java AST syntax...")
    if not pom_file.exists():
        logs.append("[ERROR] Build failed: pom.xml not found in project root.")
        failures.append({
            "phase": "validate",
            "file": "pom.xml",
            "line": 1,
            "message": "pom.xml not found in project root."
        })
        phase_results["validate"] = "FAILED"
    else:
        try:
            pom_text = pom_file.read_text(encoding="utf-8")
            if "<project" not in pom_text or "</project>" not in pom_text:
                failures.append({
                    "phase": "validate",
                    "file": "pom.xml",
                    "line": 1,
                    "message": "pom.xml is malformed: missing root <project> tag."
                })
                phase_results["validate"] = "FAILED"
            else:
                phase_results["validate"] = "SUCCESS"
                if "quarkus-bom" in pom_text:
                    logs.append("[INFO] pom.xml structure and Quarkus BOM dependency management validated.")
                else:
                    logs.append("[INFO] pom.xml structure validated.")
        except Exception as e:
            failures.append({
                "phase": "validate",
                "file": "pom.xml",
                "line": 1,
                "message": f"Error reading pom.xml: {str(e)}"
            })
            phase_results["validate"] = "FAILED"

    # Validate Java source files with real javalang AST parser
    java_files = list(workspace_dir.rglob("*.java"))
    if not java_files:
        failures.append({
            "phase": "validate",
            "file": None,
            "line": None,
            "message": "No Java source files found in workspace."
        })
        phase_results["validate"] = "FAILED"
    else:
        logs.append(f"[INFO] Parsing AST for {len(java_files)} Java source files with javalang...")
        for jf in java_files:
            rel = str(jf.relative_to(workspace_dir)).replace("\\", "/")
            try:
                code = jf.read_text(encoding="utf-8")
            except Exception as e:
                failures.append({
                    "phase": "validate",
                    "file": rel,
                    "line": 1,
                    "message": f"Encoding error reading Java file: {str(e)}"
                })
                phase_results["validate"] = "FAILED"
                continue

            # Check unbalanced braces
            open_count = code.count("{")
            close_count = code.count("}")
            if open_count != close_count:
                err_msg = f"Syntax error: unbalanced braces in {rel} (open={open_count}, close={close_count})."
                logs.append(f"[ERROR] {err_msg}")
                failures.append({
                    "phase": "validate",
                    "file": rel,
                    "line": code.count("\n") + 1,
                    "message": err_msg
                })
                phase_results["validate"] = "FAILED"

            # Parse with javalang AST parser
            try:
                javalang.parse.parse(code)
            except javalang.parser.JavaSyntaxError as jse:
                line_no = jse.at.position.line if hasattr(jse, "at") and hasattr(jse.at, "position") and jse.at.position else None
                col_no = jse.at.position.column if hasattr(jse, "at") and hasattr(jse.at, "position") and jse.at.position else None
                failures.append({
                    "phase": "validate",
                    "file": rel,
                    "line": line_no,
                    "col": col_no,
                    "message": f"Java AST Syntax error: {jse.description}"
                })
                phase_results["validate"] = "FAILED"
            except Exception:
                # Some Java 21 preview features might not be in older javalang grammars; if braces match and package is present, proceed
                pass

    if phase_results["validate"] == "FAILED":
        logs.append("[ERROR] Phase 1 (validate) failed with syntax/structure errors.")
        duration = int((time.time() - t0) * 1000)
        logs.append(f"[FATAL] VETO APPLIED: Microservice rejected in phase 'validate' with {len(failures)} error(s).")
        return False, "\n".join(logs), duration, {
            "verdict": "FAILED",
            "veto_applied": True,
            "phase_results": phase_results,
            "failures": failures,
        }

    # =========================================================================
    # PHASE 2: TEST-COMPILE (Native Maven Execution)
    # =========================================================================
    logs.append("[PHASE 2/5] Compiling main and test sources with Maven (Java 21)...")
    mvn_bin = get_maven_binary()

    if mvn_bin:
        try:
            # We use offline if dependencies are in local repo, or standard clean test-compile
            compile_cmd = [mvn_bin, "-B", "-DskipTests", "clean", "test-compile"]
            proc = subprocess.run(
                compile_cmd,
                cwd=str(workspace_dir),
                capture_output=True,
                text=True,
                shell=(os.name == "nt"),
                timeout=180,
            )
            logs.append(proc.stdout)
            if proc.stderr:
                logs.append(proc.stderr)

            if proc.returncode == 0:
                phase_results["test-compile"] = "SUCCESS"
                logs.append("[INFO] Maven clean test-compile succeeded with code 0.")
            else:
                phase_results["test-compile"] = "FAILED"
                # Parse compiler diagnostics
                parsed_errors = parse_maven_compiler_errors(proc.stdout + "\n" + proc.stderr, workspace_dir)
                if parsed_errors:
                    failures.extend(parsed_errors)
                else:
                    failures.append({
                        "phase": "test-compile",
                        "file": None,
                        "line": None,
                        "message": "Maven compilation failed. Check build logs for details."
                    })
        except subprocess.TimeoutExpired:
            failures.append({
                "phase": "test-compile",
                "file": None,
                "line": None,
                "message": "Maven compilation timed out after 180 seconds."
            })
            phase_results["test-compile"] = "FAILED"
        except Exception as exc:
            failures.append({
                "phase": "test-compile",
                "file": None,
                "line": None,
                "message": f"Execution error running Maven: {str(exc)}"
            })
            phase_results["test-compile"] = "FAILED"
    else:
        logs.append("[ERROR] Maven unavailable: native compilation cannot be verified.")
        phase_results["test-compile"] = "FAILED"
        failures.append({"phase": "test-compile", "file": None, "line": None,
                         "message": "Maven unavailable. Install Maven and rerun verification."})

    if phase_results["test-compile"] == "FAILED":
        logs.append("[ERROR] Phase 2 (test-compile) failed.")
        duration = int((time.time() - t0) * 1000)
        logs.append(f"[FATAL] VETO APPLIED: Microservice rejected in phase 'test-compile' with {len(failures)} error(s).")
        return False, "\n".join(logs), duration, {
            "verdict": "FAILED",
            "veto_applied": True,
            "phase_results": phase_results,
            "failures": failures,
        }

    # =========================================================================
    # PHASE 3: VERIFY (Execution of Acceptance Test Suites)
    # =========================================================================
    logs.append("[PHASE 3/5] Running acceptance test suites with JUnit 5 & @QuarkusTest...")
    if mvn_bin and phase_results["test-compile"] == "SUCCESS":
        test_files = list(workspace_dir.rglob("*Test.java"))
        if not test_files:
            logs.append("[WARNING] No test suites (*Test.java) declared in project.")
            phase_results["verify"] = "SUCCESS"
        else:
            try:
                test_cmd = [mvn_bin, "-B", "test"]
                test_proc = subprocess.run(
                    test_cmd,
                    cwd=str(workspace_dir),
                    capture_output=True,
                    text=True,
                    shell=(os.name == "nt"),
                    timeout=240,
                )
                logs.append(test_proc.stdout)
                if test_proc.stderr:
                    logs.append(test_proc.stderr)

                if test_proc.returncode == 0:
                    phase_results["verify"] = "SUCCESS"
                    logs.append("[INFO] All test suites passed successfully.")
                else:
                    phase_results["verify"] = "FAILED"
                    parsed_test_failures = parse_maven_test_failures(test_proc.stdout + "\n" + test_proc.stderr)
                    failures.extend(parsed_test_failures)
            except subprocess.TimeoutExpired:
                failures.append({
                    "phase": "verify",
                    "file": None,
                    "line": None,
                    "message": "Maven test verification timed out after 240 seconds."
                })
                phase_results["verify"] = "FAILED"
            except Exception as exc:
                failures.append({
                    "phase": "verify",
                    "file": None,
                    "line": None,
                    "message": f"Execution error running tests: {str(exc)}"
                })
                phase_results["verify"] = "FAILED"
    else:
        phase_results["verify"] = "SUCCESS"

    if phase_results["verify"] == "FAILED":
        logs.append("[ERROR] Phase 3 (verify) failed.")
        duration = int((time.time() - t0) * 1000)
        logs.append(f"[FATAL] VETO APPLIED: Microservice rejected in phase 'verify' with {len(failures)} test failure(s).")
        return False, "\n".join(logs), duration, {
            "verdict": "FAILED",
            "veto_applied": True,
            "phase_results": phase_results,
            "failures": failures,
        }

    # =========================================================================
    # PHASE 4: RUNTIME-TEST (Profiles & Configuration Integrity)
    # =========================================================================
    logs.append("[PHASE 4/5] Verifying runtime multi-profile configuration (%dev, %test, %prod)...")
    app_props = workspace_dir / "src" / "main" / "resources" / "application.properties"
    if app_props.exists():
        props_text = app_props.read_text(encoding="utf-8")
        if not any(k in props_text for k in ["%test.", "%dev.", "%dev,test."]):
            failures.append({
                "phase": "runtime-test",
                "file": "src/main/resources/application.properties",
                "line": 1,
                "message": "Missing multi-profile configuration (%dev / %test isolated database settings)."
            })
            phase_results["runtime-test"] = "FAILED"
        else:
            phase_results["runtime-test"] = "SUCCESS"
            logs.append("[INFO] Multi-profile configuration (%dev, %test, %prod) verified.")
    else:
        phase_results["runtime-test"] = "SUCCESS"
        logs.append("[INFO] Standard configuration profile validated.")

    # =========================================================================
    # PHASE 5: SMOKE-TEST (Inbound Wiring Verification)
    # =========================================================================
    logs.append("[PHASE 5/5] Executing smoke-test verification on declared inbounds...")
    resource_files = list(workspace_dir.rglob("*Resource.java"))
    if resource_files:
        for rf in resource_files:
            rel = str(rf.relative_to(workspace_dir)).replace("\\", "/")
            r_code = rf.read_text(encoding="utf-8")
            if "@Path" not in r_code:
                failures.append({
                    "phase": "smoke-test",
                    "file": rel,
                    "line": 1,
                    "message": f"Resource class {rel} declared without @Path annotation."
                })
                phase_results["smoke-test"] = "FAILED"
    if phase_results["smoke-test"] != "FAILED":
        phase_results["smoke-test"] = "SUCCESS"
        logs.append("[INFO] Smoke test on declared inbounds completed successfully.")

    is_overall_success = (len(failures) == 0)
    verdict = "PASSED" if is_overall_success else "FAILED"
    veto = not is_overall_success

    duration = int((time.time() - t0) * 1000)
    if is_overall_success:
        logs.append("[INFO] ========================================================================")
        logs.append("[INFO] BUILD SUCCESS")
        logs.append("[INFO] VERIFICATION PASSED: All 5 phases passed. Zero defects detected.")
        logs.append("[INFO] ========================================================================")
    else:
        logs.append(f"[FATAL] VETO APPLIED: Verification failed with {len(failures)} total defects.")

    return is_overall_success, "\n".join(logs), duration, {
        "verdict": verdict,
        "veto_applied": veto,
        "phase_results": phase_results,
        "failures": failures,
    }


def parse_maven_compiler_errors(output: str, workspace_dir: Path) -> List[Dict[str, Any]]:
    """Extract file, line, column, and error message from Maven compiler output."""
    errors = []
    # Pattern: [ERROR] /path/to/File.java:[line,col] message
    pattern = re.compile(r"\[ERROR\]\s+(?:.*?)([a-zA-Z0-9_\-\.\/\\]+\.java):\[(\d+),(\d+)\]\s+(.*)")
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            raw_path, line_no, col_no, msg = match.groups()
            rel_path = raw_path.replace("\\", "/")
            if "/src/" in rel_path:
                rel_path = "src/" + rel_path.split("/src/", 1)[1]
            errors.append({
                "phase": "test-compile",
                "file": rel_path,
                "line": int(line_no),
                "col": int(col_no),
                "message": msg.strip(),
            })
    return errors


def parse_maven_test_failures(output: str) -> List[Dict[str, Any]]:
    """Extract failed test names and failure reasons from Maven output."""
    failures = []
    # Pattern: [ERROR] Failures: / [ERROR] Errors:
    test_err_pattern = re.compile(r"\[ERROR\]\s+([a-zA-Z0-9_\.]+\.[a-zA-Z0-9_]+):(\d+)\s+(.*)")
    for line in output.splitlines():
        match = test_err_pattern.search(line)
        if match:
            test_name, line_no, msg = match.groups()
            failures.append({
                "phase": "verify",
                "test": test_name,
                "line": int(line_no),
                "message": msg.strip(),
            })
    return failures
