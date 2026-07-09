from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.aemeath_mornye_lynae_policy_probability_diagnostic import run_policy_probability_diagnostic


def main() -> None:
    report = run_policy_probability_diagnostic()
    assert report["model_probability_status"] == "not_requested"
    states = {state["state"]: state for state in report["states"]}
    for state_name in (
        "A_initial_mornye",
        "B_after_swap_to_aemeath",
        "C_aemeath_concerto_forced_100",
        "D_after_swap_to_lynae_intro",
        "E_after_lynae_resonance_skill",
        "F_after_lynae_spark_collision",
    ):
        assert state_name in states
    assert "swap_to_lynae" in states["C_aemeath_concerto_forced_100"]["valid_action_ids"]
    assert "lynae_spark_collision" in states["E_after_lynae_resonance_skill"]["valid_action_ids"]
    assert "lynae_polychrome_leap" in states["F_after_lynae_spark_collision"]["valid_action_ids"]
    print("aemeath_mornye_lynae_policy_probability_diagnostic_smoke_test ok")


if __name__ == "__main__":
    main()
