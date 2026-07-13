from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="guarded-failure-resume-") as temp_dir:
        root = Path(temp_dir)
        _run(["--execute", "--smoke-run", "--output-root", str(root)])
        state_path = root / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        branch_id, record = _first_checkpoint_record_with_branch(state)
        checkpoint = Path(record["checkpoint_path"])
        checkpoint_sha = _sha256(checkpoint)
        checkpoint_mtime = checkpoint.stat().st_mtime_ns
        Path(record["summary_path"]).unlink()
        Path(record["timeline_path"]).unlink()
        record["status"] = "checkpoint_saved"
        for key in ("summary_path", "timeline_path", "summary_sha256", "timeline_sha256", "completed_at"):
            record.pop(key, None)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

        _run(["--execute", "--smoke-run", "--resume", "--only-branch", branch_id, "--max-chunks", "1", "--output-root", str(root)])
        assert _sha256(checkpoint) == checkpoint_sha
        assert checkpoint.stat().st_mtime_ns == checkpoint_mtime
        resumed = json.loads(state_path.read_text(encoding="utf-8"))
        completed = _checkpoint_record(resumed, branch_id)
        assert completed["status"] == "completed"
        assert Path(completed["summary_path"]).exists()
        assert Path(completed["timeline_path"]).exists()
    print("guarded_ppo_failure_resume_smoke_test ok")


def _first_checkpoint_record_with_branch(state: dict[str, object]) -> tuple[str, dict[str, object]]:
    branches = state["branches"]
    assert isinstance(branches, dict)
    for branch_id, branch_state in branches.items():
        for chunk in branch_state["chunks"]:
            if chunk.get("kind") == "guarded_ppo_checkpoint":
                return str(branch_id), chunk
    raise AssertionError("no checkpoint record found")


def _checkpoint_record(state: dict[str, object], branch_id: str) -> dict[str, object]:
    for chunk in state["branches"][branch_id]["chunks"]:
        if chunk.get("kind") == "guarded_ppo_checkpoint":
            return chunk
    raise AssertionError(f"missing checkpoint for {branch_id}")


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
        }
    )
    return env


if __name__ == "__main__":
    main()
