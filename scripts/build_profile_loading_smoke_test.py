from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.build_profiles import load_build_profiles, resolve_character_build_stats
from simulator.models import CharacterData
from simulator.simulation import Simulation


def test_build_profiles_load() -> None:
    data = load_build_profiles(DATA_DIR)
    profiles = data["profiles"]
    assert "default" in profiles["aemeath"]
    assert "component_test" in profiles["aemeath"]
    assert "liberation_focus_test" in profiles["aemeath"]
    assert "aemeath_real_manual" in profiles["aemeath"]
    assert "default" in profiles["mornye"]
    assert "support_er_component_test" in profiles["mornye"]
    assert "support_er_cap" in profiles["mornye"]
    assert "mornye_real_manual" in profiles["mornye"]


def test_missing_profile_fails_clearly() -> None:
    base = Simulation.from_json(DATA_DIR, party="aemeath").all_characters["aemeath"]
    try:
        resolve_character_build_stats(base, "missing_profile", load_build_profiles(DATA_DIR))
    except ValueError as exc:
        assert "Unknown build profile" in str(exc)
        assert "missing_profile" in str(exc)
    else:
        raise AssertionError("Missing build profile should fail clearly.")


def test_energy_regen_default_and_no_mutation() -> None:
    base = CharacterData(id="future_test", name="Future Test", resonance_energy=0.0, concerto_energy=0.0)
    effective = resolve_character_build_stats(base, None, {"schema_version": 1, "profiles": {}})
    assert effective.energy_regen == 1.0
    assert base.energy_regen == 1.0
    effective.energy_regen = 2.0
    assert base.energy_regen == 1.0


def test_profile_resolution_does_not_mutate_base_character() -> None:
    base_sim = Simulation.from_json(DATA_DIR, party="aemeath")
    base = base_sim.characters["aemeath"]
    original_er = base.energy_regen
    effective = resolve_character_build_stats(base, "liberation_focus_test", load_build_profiles(DATA_DIR))
    assert effective is not base
    assert effective.build_profile_id == "liberation_focus_test"
    assert effective.static_attack > 0.0
    assert effective.effective_attack == effective.static_attack
    assert effective.damage_bonuses["by_category"]["resonance_liberation"] == 0.6
    assert base.energy_regen == original_er
    assert "resonance_liberation" not in (base.damage_bonuses.get("by_category") or {})


if __name__ == "__main__":
    test_build_profiles_load()
    test_missing_profile_fails_clearly()
    test_energy_regen_default_and_no_mutation()
    test_profile_resolution_does_not_mutate_base_character()
    print("build_profile_loading_smoke_test ok")
