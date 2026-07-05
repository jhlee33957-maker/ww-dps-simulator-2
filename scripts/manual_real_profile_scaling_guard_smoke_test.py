from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


def test_mornye_real_manual_cannot_pass_with_only_atk_fields() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        party="mornye",
        build_profile_overrides={"mornye": "mornye_real_manual"},
        stat_overrides={
            "mornye": {
                "character_base_atk": 900,
                "weapon_base_atk": 500,
                "static_atk_percent": 0.5,
                "static_flat_atk": 300,
                "final_attack_reference": 2400,
            }
        },
    )
    validation = sim.validate_build_profiles()
    assert validation["ok"] is False
    message = "\n".join(validation["errors"])
    assert "stat_components.def.character_base" in message
    assert "stat_components.def.percent" in message


def test_test_profiles_allowed_with_scaling_warnings() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    validation = sim.validate_build_profiles()
    assert validation["ok"] is True
    assert validation["warnings"]
    assert sim.effective_build_stats_summary["mornye"]["effective_def"] > 0
    assert sim.effective_build_stats_summary["mornye"]["actions_requiring_def_stats"]


def main() -> None:
    test_mornye_real_manual_cannot_pass_with_only_atk_fields()
    test_test_profiles_allowed_with_scaling_warnings()
    print("manual_real_profile_scaling_guard_smoke_test ok")


if __name__ == "__main__":
    main()
