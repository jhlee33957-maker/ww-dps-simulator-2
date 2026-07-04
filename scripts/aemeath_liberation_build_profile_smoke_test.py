from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.simulation import Simulation


def run_action(action_id: str, profile: str | None = None):
    overrides = {"aemeath": profile} if profile else None
    sim = Simulation.from_json(DATA_DIR, party="aemeath", build_profile_overrides=overrides)
    assert sim.execute_action(action_id), f"{action_id} should execute"
    return sim.timeline[-1]


def test_liberation_profile_increases_overdrive_not_basic() -> None:
    basic_default = run_action("aemeath_basic_attack")
    basic_liberation = run_action("aemeath_basic_attack", "liberation_focus_test")
    assert basic_liberation.damage_category == "basic_attack"
    assert basic_liberation.category_dmg_bonus == 0.0
    assert abs(basic_liberation.normal_damage - basic_default.normal_damage) < 1e-6

    overdrive_default = run_action("aemeath_resonance_liberation")
    overdrive_liberation = run_action("aemeath_resonance_liberation", "liberation_focus_test")
    assert overdrive_liberation.resolved_action_id == "aemeath_liberation_overdrive"
    assert overdrive_liberation.damage_category == "resonance_liberation"
    assert overdrive_liberation.category_dmg_bonus > 0.0
    assert overdrive_liberation.normal_damage > overdrive_default.normal_damage


def test_finale_uses_liberation_category() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath", build_profile_overrides={"aemeath": "liberation_focus_test"})
    state = sim.state.character_states["aemeath"]
    state["heavenfall_unbound"] = True
    state["heavenfall_unbound_remaining"] = 30.0
    state["synchronization_rate"] = 200.0
    state["resonance_rate"] = 4
    state["finale_available"] = True
    assert sim.execute_action("aemeath_resonance_liberation")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "aemeath_heavenfall_finale"
    assert row.damage_category == "resonance_liberation"
    assert row.category_dmg_bonus > 0.0


if __name__ == "__main__":
    test_liberation_profile_increases_overdrive_not_basic()
    test_finale_uses_liberation_category()
    print("aemeath_liberation_build_profile_smoke_test ok")
