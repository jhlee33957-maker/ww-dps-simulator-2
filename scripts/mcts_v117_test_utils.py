from __future__ import annotations

import copy
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_plan import load_mcts_plan


PLAN_PATH = ROOT / "data" / "mcts_plan_v117_32gb.json"


def plan_and_stage(*, simulations: int, combat_duration: float = 4.0, checkpoint_interval: int = 50,
                   limit_interval: int = 16, maximum_nodes: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = load_mcts_plan(PLAN_PATH)
    stage = copy.deepcopy(plan["stages"][0])
    stage.update({"stage_id": f"fixture_{simulations}_{combat_duration:g}", "maximum_simulations": simulations,
                  "maximum_nodes": maximum_nodes or simulations + 2, "combat_duration": float(combat_duration),
                  "checkpoint_interval_simulations": checkpoint_interval, "limit_check_interval_simulations": limit_interval,
                  "wall_clock_budget_seconds": 600, "canonical_output_root": "temporary_fixture_only"})
    return plan, stage


def directory_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(item.relative_to(path).as_posix().encode()); digest.update(item.read_bytes())
    return digest.hexdigest()


def compact_probe(result: dict[str, Any], resolved_hash: str | None = None) -> dict[str, Any]:
    best = result.get("best_completed_route") or {}
    return {"logical_result_sha256": result["logical_result_sha256"], "rng_final_state_sha256": result["rng_final_state_sha256"],
            "mast_logical_sha256": result["mast_logical_sha256"], "best_damage": best.get("total_damage"),
            "best_selected_sha256": best.get("selected_sequence_sha256"), "best_resolved_sha256": resolved_hash,
            "completed_rollout_count": result["completed_rollout_count"], "node_count": result["node_count"]}


def run_isolated_probe_worker(*, root: Path, output: Path, result_path: Path,
                              timeout_seconds: float = 180.0) -> tuple[dict[str, Any], bool]:
    command = [sys.executable, "scripts/mcts_probe_worker_v117.py", "--output-root", str(output),
               "--json-output", str(result_path)]
    kwargs: dict[str, Any] = {"cwd": root, "text": True, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "nt": kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else: kwargs["start_new_session"] = True
    process = subprocess.Popen(command, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        _terminate_process_group(process)
        stdout, stderr = process.communicate(timeout=15)
        raise TimeoutError(f"MCTS probe worker exceeded {timeout_seconds}s\n{stdout}\n{stderr}") from error
    if process.returncode:
        raise RuntimeError(stdout + stderr)
    no_survivor = process.poll() is not None
    if not no_survivor:
        _terminate_process_group(process)
        raise RuntimeError("MCTS probe worker survived normal completion")
    return json.loads(result_path.read_text(encoding="utf-8")), no_survivor


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=15)
    else:
        try: os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError: return
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
