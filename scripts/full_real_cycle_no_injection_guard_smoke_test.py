from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "full_real_cycle_integration.py"
FORBIDDEN_STATE_ATTRIBUTES = {
    "active_character_id",
    "resonance_energy",
    "concerto_energy",
    "enemy_off_tune_current",
    "enemy_tune_break_available",
    "enemy_tune_break_cooldown_remaining",
    "rupturous_trail_stacks",
    "rupturous_trail_remaining",
    "interfered_marker_remaining",
    "cooldowns",
    "scheduled_effects",
}


def attribute_chain(node: ast.AST) -> list[str]:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return list(reversed(parts))


def target_nodes(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        if isinstance(node, ast.Assign):
            return list(node.targets)
        return [node.target]
    return []


def main() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(RUNNER))
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for target in target_nodes(node):
                chain = attribute_chain(target)
                if "state" in chain and any(attr in chain for attr in FORBIDDEN_STATE_ATTRIBUTES):
                    violations.append(f"state mutation assignment at line {node.lineno}: {'.'.join(chain)}")
                if isinstance(target, ast.Subscript):
                    sub_chain = attribute_chain(target.value)
                    if "state" in sub_chain:
                        violations.append(f"state subscript assignment at line {node.lineno}")
        if isinstance(node, ast.Call):
            func_chain = attribute_chain(node.func)
            if func_chain and func_chain[-1] == "setattr":
                violations.append(f"setattr call at line {node.lineno}")
            if func_chain and func_chain[-1] in {"run_sequence", "advance_scheduled_effects"}:
                violations.append(f"forbidden direct driver call at line {node.lineno}: {'.'.join(func_chain)}")
            if func_chain and func_chain[-1] == "WuwaDpsEnv":
                violations.append(f"WuwaDpsEnv usage at line {node.lineno}")

    spec = importlib.util.spec_from_file_location("full_real_cycle_integration_guard_target", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert "short_wait" not in module.SELECTED_ROUTE
    assert "short_wait" not in module.EXPECTED_RESOLVED_ROUTE
    assert "is_action_available" in source
    assert "execute_action" in source
    assert "Simulation.from_json" in source
    assert not violations, violations
    print("full_real_cycle_no_injection_guard_smoke_test ok")


if __name__ == "__main__":
    main()
