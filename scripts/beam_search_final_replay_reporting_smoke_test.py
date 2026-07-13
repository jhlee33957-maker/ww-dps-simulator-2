from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_reporting import replay_selected_route_to_files, verified_bc_incumbent_manifest  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="beam-replay-") as output:
        search = _run_search(Path(output), 2000)
        terminal = search["best_completed_search_route"]
        assert terminal is not None
        summary = search["route_replay_summaries"][0]
        summary_path = Path(output) / summary["summary_path"]
        timeline_path = Path(output) / summary["timeline_csv_path"]
        assert summary_path.exists()
        assert timeline_path.exists()
        assert json.loads(summary_path.read_text(encoding="utf-8")) == summary
        with timeline_path.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
    assert summary["schema_version"] == "beam_search_route_replay_summary_v111"
    assert summary["total_damage"] == terminal["total_damage"]
    assert summary["selected_sequence_sha256"] == terminal["selected_sequence_sha256"]
    assert summary["resolved_sequence_sha256"] == terminal["resolved_sequence_sha256"]
    assert summary["executed_action_count"] == len(rows) == terminal["action_count"]
    assert summary["party"] == "aemeath_mornye_lynae_enabled_test_party"
    assert summary["active_build_profiles"]["mornye"]["build_profile_id"] == "mornye_user_real_01"
    assert abs(sum(summary["damage_by_character"].values()) - summary["total_damage"]) <= 1e-6
    assert abs(summary["effective_damage_role_breakdown"]["total_damage_delta"]) <= 1e-6
    incumbent = verified_bc_incumbent_manifest()
    for key in ("model_path", "model_sha256", "total_damage", "dps", "selected_sequence_sha256", "resolved_sequence_sha256", "externally_verified_immutable", "selection_reason", "objective", "global_optimum_proven"):
        assert key in incumbent
    print("beam_search_final_replay_reporting_smoke_test ok")


def _run_search(output: Path, max_expansions: int) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            "search/run_beam_search.py",
            "--plan",
            "data/beam_search_plan_v111.json",
            "--execute",
            "--smoke-run",
            "--output-root",
            str(output),
            "--max-expansions",
            str(max_expansions),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads(result.stdout)
    return json.loads(Path(summary["execution_result_path"]).read_text(encoding="utf-8"))


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    return env


if __name__ == "__main__":
    main()
