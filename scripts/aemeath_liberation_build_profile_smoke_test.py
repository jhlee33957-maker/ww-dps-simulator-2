from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


LIBERATION_DAMAGE_ACTIONS = [
    "aemeath_liberation_overdrive",
    "aemeath_heavenfall_finale",
    "aemeath_seraphic_duet_overturn",
    "aemeath_seraphic_duet_encore",
    "aemeath_heavy_aemeath_charged_1",
    "aemeath_heavy_aemeath_charged_2",
    "aemeath_heavy_mech_charged_1",
    "aemeath_heavy_mech_charged_2",
]
SERAPHIC_ACTIONS = {"aemeath_seraphic_duet_overturn", "aemeath_seraphic_duet_encore"}


def run_action(action_id: str, profile: str | None = None):
    overrides = {"aemeath": profile} if profile else None
    sim = Simulation.from_json(DATA_DIR, party="aemeath", build_profile_overrides=overrides)
    state = sim.state.character_states["aemeath"]
    if "mech" in action_id:
        state["form"] = "mech"
    if action_id in SERAPHIC_ACTIONS:
        state["form"] = "mech" if action_id.endswith("_encore") else "aemeath"
        state["synchronization_rate"] = 100.0
        state["seraphic_duo_remaining"] = 5.0
    if action_id == "aemeath_heavenfall_finale":
        state["heavenfall_unbound"] = True
        state["heavenfall_unbound_remaining"] = 30.0
        state["synchronization_rate"] = 200.0
        state["resonance_rate"] = 4.0
        state["finale_available"] = True
    assert sim.execute_action(action_id), f"{action_id} should execute"
    return sim.timeline[-1]


def test_liberation_profile_increases_liberation_damage_not_basic() -> None:
    basic_default = run_action("aemeath_basic_form_stage_1")
    basic_liberation = run_action("aemeath_basic_form_stage_1", "liberation_focus_test")
    assert basic_liberation.damage_bonus_category == "basic_attack"
    assert basic_liberation.category_dmg_bonus == 0.0
    assert abs(basic_liberation.normal_damage - basic_default.normal_damage) < 1e-6

    for action_id in LIBERATION_DAMAGE_ACTIONS:
        default = run_action(action_id)
        liberation = run_action(action_id, "liberation_focus_test")
        assert liberation.damage_bonus_category == "resonance_liberation", action_id
        assert liberation.category_dmg_bonus > 0.0, action_id
        assert liberation.normal_damage > default.normal_damage, action_id


def main() -> None:
    test_liberation_profile_increases_liberation_damage_not_basic()
    print("aemeath_liberation_build_profile_smoke_test ok")


if __name__ == "__main__":
    main()
