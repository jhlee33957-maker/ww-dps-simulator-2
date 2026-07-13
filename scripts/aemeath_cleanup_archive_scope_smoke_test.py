from __future__ import annotations

import subprocess
import sys
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GIT = shutil.which("git") or str(
    Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "native" / "git" / "cmd" / "git.exe"
)
OBSOLETE_BC_FILES = [
    "bc_eval_bundle/maskable_ppo_aemeath_mornye_lynae_bc_init.zip.bc_metadata.json",
    "bc_eval_bundle/policy_probability_bc_curr_300k.json",
    "bc_eval_bundle/policy_probability_bc_init.json",
    "bc_eval_bundle/ppo_evaluation_summary_bc_curr_300k.json",
    "bc_eval_bundle/ppo_evaluation_summary_bc_init.json",
    "bc_eval_bundle/ppo_timeline_bc_curr_300k.csv",
    "bc_eval_bundle/ppo_timeline_bc_init.csv",
    "bc_eval_bundle/training_metadata.json",
]
GENERATED_AUDIT_FILES = [
    "data/extracted/aemeath_coeff_resource_candidates.json",
    "data/extracted/aemeath_coeff_resource_unresolved.json",
    "data/extracted/aemeath_excel_actions.json",
    "data/extracted/aemeath_excel_unmapped_rows.json",
    "data/extracted/aemeath_timing_candidates.json",
    "data/extracted/aemeath_timing_unresolved.json",
    "reports/aemeath_excel_diff.md",
    "reports/aemeath_timing_review.md",
]
RUNTIME_FILES = [
    "characters/aemeath.py",
    "simulator/models.py",
    "simulator/simulation.py",
    "env/observation_features.py",
    "env/wuwa_env.py",
    "env/reward.py",
    "data/actions.json",
    "data/transition_actions.json",
    "direct_action_data_patch_manifest_v61.json",
    "data/source/direct_action_data_patch_manifest_v61.json",
]


def git_diff_name_only(paths: list[str]) -> list[str]:
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "NUL"
    result = subprocess.run(
        [GIT, "diff", "--name-only", "--", *paths],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    present = [path for path in OBSOLETE_BC_FILES if (ROOT / path).exists()]
    assert not present, present
    assert git_diff_name_only(GENERATED_AUDIT_FILES) == []
    assert git_diff_name_only(RUNTIME_FILES) == []

    subprocess.run(
        [sys.executable, "scripts/apply_direct_action_data_v61.py", "--check", "--fail-on-diff"],
        cwd=ROOT,
        check=True,
    )
    from env.observation_features import OBSERVATION_VERSION, build_observation_labels

    assert OBSERVATION_VERSION == "slot_generic_mechanics_v5"
    assert len(build_observation_labels()) == 314
    print("aemeath_cleanup_archive_scope_smoke_test ok")


if __name__ == "__main__":
    main()
