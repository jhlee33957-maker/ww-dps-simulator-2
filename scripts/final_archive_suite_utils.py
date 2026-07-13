from __future__ import annotations

import importlib.util
import ast
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script_mains(suite_name: str, script_names: tuple[str, ...]) -> None:
    """Run lightweight smoke-test mains in one interpreter with named failures."""
    suite_started = time.perf_counter()
    print(f"{suite_name} start: checks={len(script_names)}", flush=True)
    for index, script_name in enumerate(script_names):
        check_started = time.perf_counter()
        path = ROOT / "scripts" / script_name
        module_name = f"_{suite_name}_{index}_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec and spec.loader, path
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            main = getattr(module, "main", None)
            assert callable(main), f"{script_name} has no callable main()"
            main()
        except BaseException as exc:
            raise AssertionError(f"{suite_name} failed: {script_name}: {exc}") from exc
        finally:
            sys.modules.pop(module_name, None)
        print(f"{suite_name} ok: {script_name} ({time.perf_counter() - check_started:.3f}s)", flush=True)
    print(f"{suite_name} finish: elapsed={time.perf_counter() - suite_started:.3f}s", flush=True)


def assert_helper_level_scripts(script_names: tuple[str, ...]) -> None:
    """Reject process/model lifecycle entry points from an imported aggregate."""
    forbidden_imports = {"subprocess", "torch", "stable_baselines3", "sb3_contrib"}
    forbidden_calls = {"run_command", "ensure_step_zero_records"}
    for script_name in script_names:
        path = ROOT / "scripts" / script_name
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".", 1)[0] for alias in node.names}
                assert not imported & forbidden_imports, (script_name, imported & forbidden_imports)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in forbidden_imports, (script_name, node.module)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in forbidden_calls, (script_name, node.func.id)
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    assert node.func.value.id != "subprocess", (script_name, node.func.attr)
        for forbidden_entrypoint in ("evaluate_maskable_ppo.py", "train_maskable_ppo.py"):
            assert forbidden_entrypoint not in source, (script_name, forbidden_entrypoint)
