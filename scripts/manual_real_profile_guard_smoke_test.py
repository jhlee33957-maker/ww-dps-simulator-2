from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import load_build_profiles, validate_effective_build_profiles
from simulator.simulation import Simulation


def test_real_manual_profiles_are_empty_and_required() -> None:
    data = load_build_profiles(DATA_DIR)
    for character_id, profile_id in (
        ("aemeath", "aemeath_real_manual"),
        ("mornye", "mornye_real_manual"),
    ):
        profile = data["profiles"][character_id][profile_id]
        assert profile["implementation_status"] == "user_supplied_required"
        required_stat = "def" if character_id == "mornye" else "atk"
        assert profile["stat_components"][required_stat]["character_base"] is None
        assert profile["stat_components"][required_stat]["percent"] is None
        assert profile["stat_components"][required_stat]["flat"] is None
        assert profile["stat_components"][required_stat]["final_reference"] is None
        assert profile["combat_stats"]["crit_rate"] is None
        assert profile["combat_stats"]["crit_damage"] is None
        assert profile["combat_stats"]["energy_regen"] is None


def test_incomplete_real_profile_validation_fails_loudly() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        build_profile_overrides={"aemeath": "aemeath_real_manual"},
    )
    validation = validate_effective_build_profiles(sim.effective_build_stats_summary)
    assert validation["ok"] is False
    message = "\n".join(validation["errors"])
    assert "aemeath:aemeath_real_manual" in message
    assert "stat_components.atk.character_base" in message
    assert "combat_stats.crit_rate" in message
    assert "damage_bonuses.by_category.resonance_liberation" in message


def test_test_assumption_profiles_are_allowed_with_warning() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_enabled_test_party",
    )
    validation = validate_effective_build_profiles(sim.effective_build_stats_summary)
    assert validation["ok"] is True
    assert validation["warnings"]
    assert sim.characters["aemeath"].implementation_status == "test_assumption"
    assert sim.characters["mornye"].implementation_status == "test_assumption"
    assert sim.characters["aemeath"].missing_required_fields
    assert sim.effective_build_stats_summary["mornye"]["actions_requiring_def_stats"]


def main() -> None:
    test_real_manual_profiles_are_empty_and_required()
    test_incomplete_real_profile_validation_fails_loudly()
    test_test_assumption_profiles_are_allowed_with_warning()
    print("manual_real_profile_guard_smoke_test ok")


if __name__ == "__main__":
    main()
