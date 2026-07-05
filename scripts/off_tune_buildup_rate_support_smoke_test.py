from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import support_stat_context
from simulator.build_profiles import load_build_profiles, resolve_character_build_stats
from simulator.models import CharacterData
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def make_mornye_sim(*, constellation: int = 0) -> Simulation:
    config = {
        "mechanics": {
            "mornye": {
                "mornye_constellation": constellation,
                "mornye_heal_event_mode": "disabled",
            }
        }
    }
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={"mornye": "mornye_user_real_01"},
        transition_config=config,
    )
    sim.state.character_states["mornye"]["rest_mass_energy"] = 100.0
    return sim


def test_defaults_and_profile_support_stats() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    assert_close(sim.characters["aemeath"].support_stats["off_tune_buildup_rate"], 1.0, "default off tune")

    profiles = load_build_profiles(DATA_DIR)
    raw_mornye = CharacterData.model_validate(
        next(item for item in json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8-sig")) if item["id"] == "mornye")
    )
    resolved = resolve_character_build_stats(raw_mornye, "mornye_user_real_01", profiles)
    assert_close(resolved.support_stats["off_tune_buildup_rate"], 1.0, "mornye user real off tune")
    resolved.energy_regen = 9.99
    assert_close(resolved.support_stats["off_tune_buildup_rate"], 1.0, "energy regen does not affect off tune")


def test_syntony_field_support_buff_and_c2() -> None:
    sim = make_mornye_sim()
    assert sim.execute_action("mornye_heavy_attack")
    context = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert_close(context["base_off_tune_buildup_rate"], 1.0, "base")
    assert_close(context["runtime_off_tune_buildup_rate_bonus"], 0.5, "syntony bonus")
    assert_close(context["current_off_tune_buildup_rate"], 1.5, "syntony current")
    assert context["c2_off_tune_bonus_active"] is False

    c2_sim = make_mornye_sim(constellation=2)
    assert c2_sim.execute_action("mornye_heavy_attack")
    c2_context = support_stat_context(c2_sim.characters["mornye"], c2_sim.state, c2_sim.buffs)
    assert_close(c2_context["runtime_off_tune_buildup_rate_bonus"], 0.7, "syntony plus c2 bonus")
    assert_close(c2_context["current_off_tune_buildup_rate"], 1.7, "syntony plus c2 current")
    assert c2_context["c2_off_tune_bonus_active"] is True


def test_source_note_exists() -> None:
    note = json.loads((DATA_DIR / "extracted" / "mornye_off_tune_buildup_rate_source_note.json").read_text(encoding="utf-8"))
    assert note["syntony_field_bonus_source"]["cell"] == "D4122"
    assert note["syntony_field_off_tune_bonus"] == 0.5
    assert note["c2_additional_bonus"] == 0.2
    assert note["c2_default_active"] is False
    assert note["energy_regen_is_not_off_tune_buildup_rate"] is True


def main() -> None:
    test_defaults_and_profile_support_stats()
    test_syntony_field_support_buff_and_c2()
    test_source_note_exists()
    print("off_tune_buildup_rate_support_smoke_test ok")


if __name__ == "__main__":
    main()
