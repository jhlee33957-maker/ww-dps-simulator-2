from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="guarded-resume-") as temp_dir:
        root = Path(temp_dir)
        base = root / "base"
        _run_runner(["--execute", "--smoke-run", "--output-root", str(base)])
        state_path = base / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        first_record = _first_checkpoint_record(state)
        checkpoint = Path(first_record["checkpoint_path"])
        checkpoint_sha = _sha256(checkpoint)
        checkpoint_mtime = checkpoint.stat().st_mtime_ns

        non_resume = _run_runner(["--execute", "--smoke-run", "--output-root", str(base)], check=False)
        assert non_resume.returncode != 0
        assert "without --resume" in non_resume.stderr

        _run_runner(["--execute", "--smoke-run", "--resume", "--output-root", str(base)])
        assert _sha256(checkpoint) == checkpoint_sha
        assert checkpoint.stat().st_mtime_ns == checkpoint_mtime

        sidecar_bad = _copy_tree(base, root / "sidecar_bad")
        sidecar_state = json.loads((sidecar_bad / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json").read_text(encoding="utf-8"))
        sidecar = Path(_first_checkpoint_record(sidecar_state)["metadata_path"])
        sidecar.write_text(sidecar.read_text(encoding="utf-8") + "\n ", encoding="utf-8")
        bad = _run_runner(["--execute", "--smoke-run", "--resume", "--output-root", str(sidecar_bad)], check=False)
        assert bad.returncode != 0
        assert "sidecar hash mismatch" in bad.stderr

        summary_bad = _copy_tree(base, root / "summary_bad")
        summary_state_path = summary_bad / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
        summary_state = json.loads(summary_state_path.read_text(encoding="utf-8"))
        summary = Path(_first_checkpoint_record(summary_state)["summary_path"])
        summary.write_text("{", encoding="utf-8")
        bad = _run_runner(["--execute", "--smoke-run", "--resume", "--output-root", str(summary_bad)], check=False)
        assert bad.returncode != 0

        eval_resume = _copy_tree(base, root / "eval_resume")
        eval_state_path = eval_resume / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
        eval_state = json.loads(eval_state_path.read_text(encoding="utf-8"))
        branch_id, record = _first_checkpoint_record_with_branch(eval_state)
        eval_checkpoint = Path(record["checkpoint_path"])
        eval_checkpoint_sha = _sha256(eval_checkpoint)
        eval_checkpoint_mtime = eval_checkpoint.stat().st_mtime_ns
        Path(record["summary_path"]).unlink()
        Path(record["timeline_path"]).unlink()
        record["status"] = "checkpoint_saved"
        for key in ("summary_path", "timeline_path", "summary_sha256", "timeline_sha256"):
            record.pop(key, None)
        eval_state_path.write_text(json.dumps(eval_state, indent=2), encoding="utf-8")
        _run_runner(["--execute", "--smoke-run", "--resume", "--only-branch", branch_id, "--max-chunks", "1", "--output-root", str(eval_resume)])
        assert _sha256(eval_checkpoint) == eval_checkpoint_sha
        assert eval_checkpoint.stat().st_mtime_ns == eval_checkpoint_mtime

    with tempfile.TemporaryDirectory(prefix="guarded-resume-missing-") as temp_dir:
        missing = _run_runner(["--execute", "--smoke-run", "--resume", "--output-root", temp_dir], check=False)
        assert missing.returncode != 0
        assert "no valid state" in missing.stderr

    with tempfile.TemporaryDirectory(prefix="guarded-nonempty-") as temp_dir:
        root = Path(temp_dir)
        populated = root / "models" / "guarded_ppo_v109_smoke"
        populated.mkdir(parents=True)
        (populated / "orphan.txt").write_text("orphan", encoding="utf-8")
        result = _run_runner(["--execute", "--smoke-run", "--output-root", str(root)], check=False)
        assert result.returncode != 0
        assert "non-empty experiment directory" in result.stderr

    invalid = _run_runner(["--execute", "--smoke-run", "--only-branch", "missing_branch"], check=False)
    assert invalid.returncode != 0
    assert "Unknown branch" in invalid.stderr
    print("guarded_ppo_resume_smoke_test ok")


def _copy_tree(source: Path, target: Path) -> Path:
    shutil.copytree(source, target)
    state_path = target / "results" / "guarded_ppo_v109_smoke" / "experiment_state.json"
    _rewrite_paths(state_path, source.resolve().as_posix(), target.resolve().as_posix())
    return target


def _rewrite_paths(path: Path, old: str, new: str) -> None:
    payload = path.read_text(encoding="utf-8").replace(old, new)
    path.write_text(payload, encoding="utf-8")


def _run_runner(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "rl/run_guarded_ppo_experiment.py", *args],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        timeout=240,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"runner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def _first_checkpoint_record(state: dict[str, object]) -> dict[str, object]:
    return _first_checkpoint_record_with_branch(state)[1]


def _first_checkpoint_record_with_branch(state: dict[str, object]) -> tuple[str, dict[str, object]]:
    branches = state["branches"]
    assert isinstance(branches, dict)
    for branch_id, branch_state in branches.items():
        for chunk in branch_state["chunks"]:
            if chunk.get("kind") == "guarded_ppo_checkpoint":
                return str(branch_id), chunk
    raise AssertionError("no checkpoint record found")


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
