from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import create_initial_state, ensure_step_zero_records, load_plan, write_json_atomic

    plan_path = ROOT / "data" / "guarded_ppo_experiment_plan_v109.json"
    plan = load_plan(plan_path)
    branch_id = "bc_conservative_seed_11"
    with tempfile.TemporaryDirectory(prefix="guarded-orphan-source-") as source_dir, tempfile.TemporaryDirectory(
        prefix="guarded-orphan-adopt-"
    ) as adopt_dir:
        source_root = Path(source_dir)
        _run(["--execute", "--smoke-run", "--only-branch", branch_id, "--max-chunks", "1", "--output-root", str(source_root)])
        source_state = json.loads((source_root / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json").read_text(encoding="utf-8"))
        source_record = next(
            chunk
            for chunk in source_state["branches"][branch_id]["chunks"]
            if chunk.get("kind") == "guarded_ppo_checkpoint"
        )
        source_checkpoint = Path(source_record["checkpoint_path"])
        source_sidecar = Path(source_record["metadata_path"])
        checkpoint_sha = _sha256(source_checkpoint)
        checkpoint_mtime = source_checkpoint.stat().st_mtime_ns

        adopt_root = Path(adopt_dir)
        checkpoint = adopt_root / "models" / "guarded_ppo_v109_smoke" / branch_id / "step_000000032.zip"
        sidecar = Path(str(checkpoint) + ".ppo_metadata.json")
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_bytes(source_checkpoint.read_bytes())
        sidecar.write_bytes(source_sidecar.read_bytes())
        os.utime(checkpoint, ns=(checkpoint_mtime, checkpoint_mtime))

        smoke_plan = json.loads(json.dumps(plan))
        smoke_plan["checkpoint_root"] = "models/guarded_ppo_v109_smoke"
        smoke_plan["results_root"] = "results/guarded_ppo_v109_smoke"
        for branch in smoke_plan["branches"]:
            branch["total_timesteps"] = 32
            branch["chunk_timesteps"] = 32
            branch["n_steps"] = 32
            branch["batch_size"] = 32
        results_root = adopt_root / smoke_plan["results_root"]
        state_path = results_root / "experiment_state.json"
        state = create_initial_state(smoke_plan, plan_path=plan_path, output_root=adopt_root, smoke_run=True)
        write_json_atomic(state_path, state)
        ensure_step_zero_records(smoke_plan, state=state, output_root=adopt_root, state_path=state_path, evaluation_timeout_seconds=120)
        branch_state = state["branches"][branch_id]
        branch_state["chunks"].append({"branch_id": branch_id, "chunk_index": 1, "status": "training_started"})
        write_json_atomic(state_path, state)

        _run(["--execute", "--smoke-run", "--resume", "--only-branch", branch_id, "--max-chunks", "1", "--output-root", str(adopt_root)])
        assert _sha256(checkpoint) == checkpoint_sha
        assert checkpoint.stat().st_mtime_ns == checkpoint_mtime
        adopted = json.loads(state_path.read_text(encoding="utf-8"))
        record = next(chunk for chunk in adopted["branches"][branch_id]["chunks"] if chunk.get("kind") == "guarded_ppo_checkpoint")
        assert record["checkpoint_adopted_from_orphan"] is True
        assert record["status"] == "completed"
    print("guarded_ppo_orphan_checkpoint_adoption_smoke_test ok")


def _run(args: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, "rl/run_guarded_ppo_experiment.py", *args],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        timeout=240,
    )
    if result.returncode != 0:
        raise AssertionError(f"runner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


if __name__ == "__main__":
    main()
