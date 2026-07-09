from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.aemeath_mornye_lynae_policy_probability_diagnostic import run_policy_probability_diagnostic
from scripts.generate_route_demonstrations import generate_route_demonstrations


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
        "G_after_lynae_intro_and_liberation",
        "H_after_lynae_intro_liberation_and_skill",
        "I_after_lynae_intro_liberation_skill_spark",
        "J_aemeath_post_liberation_concerto_ready",
    ):
        assert state_name in states
    assert "swap_to_lynae" in states["C_aemeath_concerto_forced_100"]["valid_action_ids"]
    assert "lynae_spark_collision" in states["E_after_lynae_resonance_skill"]["valid_action_ids"]
    assert "lynae_polychrome_leap" in states["F_after_lynae_spark_collision"]["valid_action_ids"]
    assert "lynae_resonance_liberation" not in states["G_after_lynae_intro_and_liberation"]["valid_action_ids"]
    assert "lynae_spark_collision" in states["H_after_lynae_intro_liberation_and_skill"]["valid_action_ids"]
    assert "lynae_polychrome_leap" in states["I_after_lynae_intro_liberation_skill_spark"]["valid_action_ids"]
    assert "aemeath_resonance_liberation" not in states["J_aemeath_post_liberation_concerto_ready"]["valid_action_ids"]
    assert "swap_to_aemeath" in states["G_after_lynae_intro_and_liberation"]["focus_actions"]
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_path = Path(temp_dir) / "route_demo.npz"
        generate_route_demonstrations(output_path=demo_path, repeat=1)
        demo_report = run_policy_probability_diagnostic(route_demo_path=demo_path)["route_demo_probability_report"]
        assert demo_report["status"] == "model_not_loaded"
        assert demo_report["sample_count"] > 0
    print("aemeath_mornye_lynae_policy_probability_diagnostic_smoke_test ok")


if __name__ == "__main__":
    main()
