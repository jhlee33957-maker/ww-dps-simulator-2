from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import party_config_hash  # noqa: E402


EXPECTED_PARTY_CONFIG_HASH = "baff722d9ce79cf7f57891c439b7b3fd746ad76e779e4d582eaa51802eba2684"
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
    actual = party_config_hash(root=ROOT)
    assert actual == EXPECTED_PARTY_CONFIG_HASH, actual
    for script in CHECKS:
        run_check(script)
    print("user_account_actual_v120_historical_party_hash_compatibility_smoke_test ok")


if __name__ == "__main__":
    main()
