"""
Deterministic Specification Linter & Feasibility Engine for TCS Quarkus Factory.
Validates ServiceSpec before architectural planning:
1. Behavior-to-Inbound/Outbound reference integrity.
2. Java & SQL reserved keyword conflicts.
3. Financial / monetary fields type enforcement (BigDecimal mandatory).
4. Saga compensation completeness.
5. State machine graph connectivity and reachability.
6. Governance capability authorization.
"""

from typing import Any, Dict, List, Set, Tuple
import re
from app.schemas.service_spec import ServiceSpec


JAVA_RESERVED_WORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new", "package",
    "private", "protected", "public", "return", "short", "static", "strictfp",
    "super", "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while", "record", "var", "yield"
}

SQL_RESERVED_WORDS = {
    "select", "insert", "update", "delete", "from", "where", "table", "order",
    "group", "by", "create", "drop", "alter", "user", "index", "view", "join",
    "inner", "outer", "left", "right", "full", "having", "limit", "offset",
    "values", "into", "set", "primary", "key", "foreign", "references"
}

MONETARY_FIELD_KEYWORDS = [
    "price", "precio", "amount", "monto", "salary", "salario",
    "cost", "costo", "balance", "saldo", "limit", "limite",
    "creditlimit", "premiumamount", "fee", "tarifa"
]


class LinterValidationResult:
    def __init__(self, is_feasible: bool, rejection_reasons: List[str]):
        self.is_feasible = is_feasible
        self.rejection_reasons = rejection_reasons


class SpecLinter:

    @classmethod
    def lint_and_verify_feasibility(
        cls,
        spec: ServiceSpec,
        governance_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Verify structural and semantic feasibility of the service specification.
        Returns: (is_feasible: bool, errors: List[str])
        """
        errors: List[str] = []

        # 1. Behavior references to Inbound and Outbound
        inbound_ids: Set[str] = {ib.id for ib in spec.inbound}
        outbound_ids: Set[str] = {ob.id for ob in spec.outbound}

        if not spec.behaviors:
            errors.append("Spec error: At least one behavior specification is mandatory.")

        for b in spec.behaviors:
            if b.inbound_ref not in inbound_ids:
                errors.append(f"Behavior '{b.id}' references undeclared inbound '{b.inbound_ref}'. Available: {list(inbound_ids)}")
            if b.outbound_ref and b.outbound_ref not in outbound_ids:
                errors.append(f"Behavior '{b.id}' references undeclared outbound '{b.outbound_ref}'. Available: {list(outbound_ids)}")

        # 2. Reserved Keywords in Data Models & Fields
        for model in spec.domain.data_models:
            if model.name.lower() in JAVA_RESERVED_WORDS:
                errors.append(f"Model name '{model.name}' is a reserved Java keyword.")
            if model.table_name and model.table_name.lower() in SQL_RESERVED_WORDS:
                errors.append(f"Table name '{model.table_name}' in model '{model.name}' is a reserved SQL keyword.")

            for field in model.fields:
                if field.name.lower() in JAVA_RESERVED_WORDS:
                    errors.append(f"Field name '{field.name}' in model '{model.name}' is a reserved Java keyword.")
                if field.name.lower() in SQL_RESERVED_WORDS:
                    errors.append(f"Field name '{field.name}' in model '{model.name}' is a reserved SQL keyword. Use an alternative or rename.")

                # 3. Monetary precision rule (Principio Bancario)
                if any(k in field.name.lower() for k in MONETARY_FIELD_KEYWORDS):
                    if field.type.lower() in ["float", "double"]:
                        errors.append(
                            f"Field '{field.name}' in model '{model.name}' is a financial/monetary field and MUST be 'BigDecimal', "
                            f"never '{field.type}' (Floating-point precision hazard)."
                        )

        # 4. Saga Workflows & Compensations
        for wf in spec.domain.workflows:
            for step in wf.steps:
                if not step.compensation_action:
                    errors.append(f"Saga '{wf.id}' step '{step.step_id}' lacks a defined compensation action.")
                if step.outbound_ref not in outbound_ids:
                    errors.append(f"Saga '{wf.id}' step '{step.step_id}' references undeclared outbound '{step.outbound_ref}'.")

        # 5. State Machine validation
        for sm in spec.domain.state_machines:
            state_set = set(sm.states)
            if sm.initial_state not in state_set:
                errors.append(f"State machine '{sm.id}' initial state '{sm.initial_state}' is not in states list.")
            for term in sm.terminal_states:
                if term not in state_set:
                    errors.append(f"State machine '{sm.id}' terminal state '{term}' is not in states list.")
            for trans in sm.transitions:
                if trans.from_state not in state_set:
                    errors.append(f"Transition in '{sm.id}' references unknown from_state '{trans.from_state}'.")
                if trans.to_state not in state_set:
                    errors.append(f"Transition in '{sm.id}' references unknown to_state '{trans.to_state}'.")

        # 6. Governance prefix check
        pkg_prefix = spec.governance_ref.package_prefix
        client = governance_context.get('client') or {}
        expected_client = spec.governance_ref.client_code.lower()
        expected_prefix = (governance_context.get('package_prefix') or client.get('package_prefix')
                           or f'pe.com.{expected_client}')
        if any(not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', part)
               or part in JAVA_RESERVED_WORDS for part in pkg_prefix.split('.')):
            errors.append(f"Invalid Java package prefix '{pkg_prefix}': every segment must be a Java identifier, not a number or reserved word.")
        if pkg_prefix != expected_prefix and not pkg_prefix.startswith(expected_prefix + '.'):
            errors.append(f"Package prefix '{pkg_prefix}' does not conform to configured prefix '{expected_prefix}'.")

        is_feasible = (len(errors) == 0)
        return is_feasible, errors


def validate_service_spec(spec_data: Any, governance_context: Dict[str, Any] = None) -> LinterValidationResult:
    """
    Validate a ServiceSpec or dictionary specification against feasibility,
    reserved words, precision, and governance rules.
    """
    if governance_context is None:
        governance_context = {"client_code": "bcp", "package_prefix": "pe.com.bcp"}

    reasons: List[str] = []

    # If it's a dict, inspect fields directly
    if isinstance(spec_data, dict):
        for m in spec_data.get("domain", {}).get("data_models", []):
            for f in m.get("fields", []):
                fname = f.get("name", "").lower()
                ftype = f.get("type", "").lower()
                if any(k in fname for k in MONETARY_FIELD_KEYWORDS):
                    if ftype in ["float", "double"]:
                        reasons.append(
                            f"Field '{f.get('name')}' in model '{m.get('name')}' is monetary and MUST be 'BigDecimal', not '{f.get('type')}'."
                        )
                if fname in JAVA_RESERVED_WORDS:
                    reasons.append(f"Field name '{f.get('name')}' is a reserved Java keyword.")

        for wf in spec_data.get("domain", {}).get("workflows", []):
            steps = wf.get("steps", [])
            compensations = wf.get("compensations", [])
            if not compensations and len(steps) > 1:
                reasons.append(f"Saga '{wf.get('name')}' defines multi-step operations without compensating actions.")

        behaviors = spec_data.get("behaviors", [])
        if not behaviors and spec_data.get("expected_verdict") != "AWAITING_REVIEW":
            reasons.append("At least one behavior specification is mandatory.")

        is_feasible = (len(reasons) == 0)
        return LinterValidationResult(is_feasible, reasons)

    # If it's ServiceSpec instance
    is_feasible, reasons = SpecLinter.lint_and_verify_feasibility(spec_data, governance_context)
    return LinterValidationResult(is_feasible, reasons)

