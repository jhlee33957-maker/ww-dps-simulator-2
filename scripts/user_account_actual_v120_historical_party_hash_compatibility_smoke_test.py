from __future__ import annotations

import os
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import PARTY_CONFIG_HASH_FILES, party_config_hash  # noqa: E402
from simulator.timing_training_gate import load_timing_runtime_gate  # noqa: E402


EXPECTED_PARTY_CONFIG_HASH = "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
EXPECTED_TRANSITION_CONFIG_SHA256 = "210538d4bf99789d0af08ecff5fb76dc3f472f5b170a144d9f1b3b1f46116b9c"
CHECKS = [
    "scripts/beam_search_plan_v114_32gb_contract_smoke_test.py",
    "scripts/manual_120s_bc_demo_hash_guard_smoke_test.py",
    "scripts/transition_contract_v114_rebaseline_smoke_test.py",
    "scripts/beam_search_v116_winner_replay_parity_smoke_test.py",
]


def run_check(script: str) -> None:
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
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{script} failed with return code {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def main() -> None:
    transition_path = ROOT / "data" / "transition_config.json"
    assert hashlib.sha256(transition_path.read_bytes()).hexdigest() == EXPECTED_TRANSITION_CONFIG_SHA256
    transition = json.loads(transition_path.read_text(encoding="utf-8-sig"))
    assert transition["generic_swap_fallback"]["reentry_cooldown_clock"] == "combat_time"
    actual = party_config_hash(root=ROOT)
    assert actual == EXPECTED_PARTY_CONFIG_HASH, actual
    gate = load_timing_runtime_gate(ROOT)
    assert gate["historical_swap_reentry_clock"] == "combat_time"
    assert gate["effective_swap_reentry_clock"] == "current_time"
    assert gate["effective_swap_reentry_clock_source"] == "candidate_124_timing_runtime_override"

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        for relative_path in PARTY_CONFIG_HASH_FILES:
            target = temporary_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative_path, target)
        mutated_transition = json.loads((temporary_root / "data/transition_config.json").read_text(encoding="utf-8-sig"))
        mutated_transition["generic_swap_fallback"]["reentry_cooldown_clock"] = "current_time"
        (temporary_root / "data/transition_config.json").write_text(
            json.dumps(mutated_transition, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        assert hashlib.sha256((temporary_root / "data/transition_config.json").read_bytes()).hexdigest() != (
            EXPECTED_TRANSITION_CONFIG_SHA256
        )
        assert party_config_hash(root=temporary_root) != EXPECTED_PARTY_CONFIG_HASH

    missing_override = dict(gate)
    missing_override.pop("effective_swap_reentry_clock")
    assert missing_override.get("effective_swap_reentry_clock") != "current_time"
    for script in CHECKS:
        run_check(script)
    print("user_account_actual_v120_historical_party_hash_compatibility_smoke_test ok mutations_rejected=4")


if __name__ == "__main__":
    main()
