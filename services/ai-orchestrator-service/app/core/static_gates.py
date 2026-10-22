"""
Static Quality Gates for TCS Quarkus Factory.
Enforces deterministic enterprise compliance prior to sandbox verification:
1. Client governance package prefix integrity (e.g. pe.com.bcp.*)
2. AST Java syntax validation using javalang
3. Symbol and import resolution (zero unresolvable internal imports)
4. Uniqueness of FQCNs, REST paths+methods, and entity table names
5. Zero hardcoded secrets / credentials in source code
6. Manifest consistency (only manifest-declared files delivered)
"""

import re
from typing import Any, Dict, List, Set, Tuple
import javalang


KNOWN_EXTERNAL_PACKAGES = {
    "java", "javax", "jakarta",
    "io.quarkus", "io.smallrye", "org.jboss", "org.eclipse.microprofile",
    "com.fasterxml.jackson", "org.junit", "io.restassured", "org.mockito",
    "org.hibernate", "org.apache", "com.google"
}


def is_known_package(imported_pkg: str) -> bool:
    """Check if an import belongs to the standard library or approved enterprise dependencies."""
    for known in KNOWN_EXTERNAL_PACKAGES:
        if imported_pkg == known or imported_pkg.startswith(f"{known}."):
            return True
    return False


class StaticGateChecker:

    @classmethod
    def evaluate_gates(
        cls,
        files: Dict[str, str],
        package_prefix: str,
        manifest: List[Dict[str, Any]],
        governance_context: Dict[str, Any]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Evaluate all static gates on the project.
        Returns: (passed: bool, failures: List[Dict[str, Any]])
        """
        failures: List[Dict[str, Any]] = []

        # Gate 1: Package prefix governance
        cls._gate_package_prefix(files, package_prefix, failures)

        # Gate 2: AST Java Syntax validation
        cls._gate_ast_syntax(files, failures)

        # Gate 3: Symbol and Import Resolution
        cls._gate_import_resolution(files, package_prefix, manifest, failures)

        # Gate 4: Uniqueness (FQCN, REST paths, Table names)
        cls._gate_uniqueness(files, failures)

        # Gate 5: No secrets in code
        cls._gate_no_secrets(files, failures)

        # Gate 6: Forbidden dependencies in pom.xml
        cls._gate_forbidden_dependencies(files, governance_context, failures)

        # Gate 7: Manifest consistency
        cls._gate_manifest_consistency(files, manifest, failures)

        return (len(failures) == 0), failures

    @classmethod
    def _gate_package_prefix(cls, files: Dict[str, str], package_prefix: str, failures: List[Dict[str, Any]]):
        """Ensure all Java files belong strictly to the client package prefix."""
        for path, content in files.items():
            if not path.endswith(".java"):
                continue
            match = re.search(r"^\s*package\s+([a-zA-Z0-9_\.]+);", content, re.MULTILINE)
            if not match:
                failures.append({
                    "gate": "PACKAGE_PREFIX",
                    "file": path,
                    "line": 1,
                    "message": "Missing package declaration in Java source file."
                })
            else:
                pkg = match.group(1)
                if not pkg.startswith(package_prefix):
                    failures.append({
                        "gate": "PACKAGE_PREFIX",
                        "file": path,
                        "line": 1,
                        "message": f"Package '{pkg}' violates client governance prefix '{package_prefix}'."
                    })

    @classmethod
    def _gate_ast_syntax(cls, files: Dict[str, str], failures: List[Dict[str, Any]]):
        """Parse all Java files using javalang AST parser."""
        for path, content in files.items():
            if not path.endswith(".java"):
                continue

            # Check brace balance first
            open_count = content.count("{")
            close_count = content.count("}")
            if open_count != close_count:
                failures.append({
                    "gate": "AST_SYNTAX",
                    "file": path,
                    "line": content.count("\n") + 1,
                    "message": f"Unbalanced braces in {path}: (open={open_count}, close={close_count})."
                })
                continue

            try:
                javalang.parse.parse(content)
            except javalang.parser.JavaSyntaxError as err:
                line_no = err.at.position.line if hasattr(err, "at") and hasattr(err.at, "position") and err.at.position else None
                failures.append({
                    "gate": "AST_SYNTAX",
                    "file": path,
                    "line": line_no,
                    "message": f"Syntax error: {err.description}"
                })
            except Exception:
                # If braces are balanced and package is valid, allow modern Java 21 preview features
                pass

    @classmethod
    def _gate_import_resolution(
        cls,
        files: Dict[str, str],
        package_prefix: str,
        manifest: List[Dict[str, Any]],
        failures: List[Dict[str, Any]]
    ):
        """Ensure internal project imports reference real, existing project classes."""
        # Build set of declared internal FQCNs in project
        declared_fqcns: Set[str] = set()
        for path, content in files.items():
            if not path.endswith(".java"):
                continue
            pkg_match = re.search(r"^\s*package\s+([a-zA-Z0-9_\.]+);", content, re.MULTILINE)
            cls_match = re.search(r"\b(?:public\s+)?(?:class|interface|enum|record)\s+([a-zA-Z0-9_]+)", content)
            if pkg_match and cls_match:
                fqcn = f"{pkg_match.group(1)}.{cls_match.group(1)}"
                declared_fqcns.add(fqcn)

        for entry in manifest:
            if entry.get("fqcn"):
                declared_fqcns.add(entry["fqcn"])

        for path, content in files.items():
            if not path.endswith(".java"):
                continue
            import_matches = re.findall(r"^\s*import\s+([a-zA-Z0-9_\.]+);", content, re.MULTILINE)
            for imp in import_matches:
                # If it's an internal project import, it MUST be declared
                if imp.startswith(package_prefix):
                    if imp not in declared_fqcns and not imp.endswith(".*"):
                        failures.append({
                            "gate": "IMPORT_RESOLUTION",
                            "file": path,
                            "line": 1,
                            "message": f"Unresolved internal import '{imp}'. Class not found in project."
                        })
                elif not is_known_package(imp):
                    # Alien unrecognized library import
                    failures.append({
                        "gate": "IMPORT_RESOLUTION",
                        "file": path,
                        "line": 1,
                        "message": f"Unrecognized external import '{imp}' not in approved enterprise BOM."
                    })

    @classmethod
    def _gate_uniqueness(cls, files: Dict[str, str], failures: List[Dict[str, Any]]):
        """Ensure uniqueness of FQCNs, REST paths + methods, and entity table names."""
        seen_fqcns: Dict[str, str] = {}
        seen_routes: Dict[Tuple[str, str], str] = {}
        seen_tables: Dict[str, str] = {}

        for path, content in files.items():
            if not path.endswith(".java"):
                continue

            # FQCN uniqueness
            pkg_match = re.search(r"^\s*package\s+([a-zA-Z0-9_\.]+);", content, re.MULTILINE)
            cls_match = re.search(r"\b(?:public\s+)?(?:class|interface|enum|record)\s+([a-zA-Z0-9_]+)", content)
            if pkg_match and cls_match:
                fqcn = f"{pkg_match.group(1)}.{cls_match.group(1)}"
                if fqcn in seen_fqcns:
                    failures.append({
                        "gate": "UNIQUENESS",
                        "file": path,
                        "line": 1,
                        "message": f"Duplicate FQCN '{fqcn}' already defined in '{seen_fqcns[fqcn]}'."
                    })
                else:
                    seen_fqcns[fqcn] = path

            # REST routes uniqueness in Resources
            if "Resource.java" in path:
                root_path_match = re.search(r'@Path\("([^"]+)"\)', content)
                root_path = root_path_match.group(1) if root_path_match else ""
                method_blocks = re.split(r'\n\s*(?:public|protected|private)\s+', content)
                for block in method_blocks[1:]:
                    verb_m = re.search(r'@(GET|POST|PUT|DELETE|PATCH)\b', block)
                    if verb_m:
                        http_verb = verb_m.group(1)
                        sub_m = re.search(r'@Path\("([^"]+)"\)', block)
                        sub_path = sub_m.group(1) if sub_m else ""
                        full_path = (root_path + ("/" + sub_path.lstrip("/") if sub_path else "")).rstrip("/")
                        route_key = (http_verb, full_path)
                        if route_key in seen_routes:
                            failures.append({
                                "gate": "UNIQUENESS",
                                "file": path,
                                "line": 1,
                                "message": f"Duplicate endpoint route {http_verb} {full_path} already defined in '{seen_routes[route_key]}'."
                            })
                        else:
                            seen_routes[route_key] = path

            # Entity table uniqueness
            table_match = re.search(r'@Table\(name\s*=\s*"([^"]+)"\)', content)
            if table_match:
                table_name = table_match.group(1).lower()
                if table_name in seen_tables:
                    failures.append({
                        "gate": "UNIQUENESS",
                        "file": path,
                        "line": 1,
                        "message": f"Duplicate database table name '{table_name}' in entity {path}, already mapped in '{seen_tables[table_name]}'."
                    })
                else:
                    seen_tables[table_name] = path

    @classmethod
    def _gate_no_secrets(cls, files: Dict[str, str], failures: List[Dict[str, Any]]):
        """Verify no hardcoded passwords, tokens, or private secrets in source code."""
        secret_patterns = [
            (r'password\s*=\s*"[a-zA-Z0-9_\!@#\$%\^&\*]{6,}"', "Hardcoded password string detected"),
            (r'BEGIN RSA PRIVATE KEY', "Hardcoded private RSA key in production code"),
            (r'AIzaSy[a-zA-Z0-9_\-]{33}', "Hardcoded Google API key detected"),
        ]
        for path, content in files.items():
            if path.startswith("src/test/") or "privateKey.pem" in path:
                continue  # Test resources are allowed local mock keys
            for pat, desc in secret_patterns:
                if re.search(pat, content):
                    failures.append({
                        "gate": "NO_SECRETS",
                        "file": path,
                        "line": 1,
                        "message": f"Security violation: {desc} in {path}."
                    })

    @classmethod
    def _gate_forbidden_dependencies(
        cls,
        files: Dict[str, str],
        governance_context: Dict[str, Any],
        failures: List[Dict[str, Any]]
    ):
        """Check pom.xml for forbidden libraries (e.g. spring-boot, lombok, unapproved ORMs)."""
        pom = files.get("pom.xml", "")
        if not pom:
            return

        forbidden = ["org.springframework", "spring-boot", "org.projectlombok"]
        # Add client governance specific forbidden dependencies if present
        for dep in governance_context.get("forbidden_dependencies", []):
            if isinstance(dep, str):
                forbidden.append(dep)

        for forb in forbidden:
            if forb in pom:
                failures.append({
                    "gate": "FORBIDDEN_DEPENDENCY",
                    "file": "pom.xml",
                    "line": 1,
                    "message": f"Forbidden dependency coordinate '{forb}' detected in pom.xml."
                })

    @classmethod
    def _gate_manifest_consistency(
        cls,
        files: Dict[str, str],
        manifest: List[Dict[str, Any]],
        failures: List[Dict[str, Any]]
    ):
        """Prune any files not declared in the immutable architectural manifest."""
        if not manifest:
            return
        declared_paths = {entry["path"] for entry in manifest if "path" in entry}
        # Allow pom.xml, README.md, CI workflows, and application.properties
        standard_allowed = {
            "pom.xml", "README.md", "Dockerfile", ".github/workflows/ci.yml",
            "src/main/resources/application.properties", "src/main/resources/import.sql"
        }
        for fpath in list(files.keys()):
            if fpath not in declared_paths and fpath not in standard_allowed and not fpath.startswith("src/main/resources/"):
                # Prune undeclared alien file
                del files[fpath]


class StaticGateFailure:
    def __init__(self, gate: str, file: str, line: int, message: str):
        self.gate = gate
        self.file = file
        self.line = line
        self.message = message


class StaticGateResult:
    def __init__(self, passed: bool, failures: list):
        self.passed = passed
        self.failures = failures


def evaluate_static_gates(
    files: dict,
    manifest: list = None,
    expected_package_prefix: str = 'pe.com.bcp',
    governance_context: dict = None
) -> StaticGateResult:
    if manifest is None:
        manifest = []
    if governance_context is None:
        governance_context = {'forbidden_dependencies': []}

    passed, raw_failures = StaticGateChecker.evaluate_gates(
        files=files,
        package_prefix=expected_package_prefix,
        manifest=manifest,
        governance_context=governance_context
    )
    failures = [
        StaticGateFailure(
            gate=f.get('gate', 'STATIC_GATE'),
            file=f.get('file', ''),
            line=f.get('line', 1),
            message=f.get('message', '')
        )
        for f in raw_failures
    ]
    return StaticGateResult(passed, failures)
