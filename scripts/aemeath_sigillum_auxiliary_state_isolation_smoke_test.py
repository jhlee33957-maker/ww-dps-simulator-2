from __future__ import annotations

import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def aemeath_state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def assert_sigillum_auxiliary_side_effects(sim: Simulation, *, previous_effect_instance_id: str | None = None) -> None:
    assert sim.state.cooldowns["aemeath_echo_sigillum"] == 20.0
    sigillum_effects = [
        effect for effect in sim.state.scheduled_effects if effect.source_action_id == "aemeath_echo_sigillum"
    ]
    assert [effect.effect_id for effect in sigillum_effects] == [
        "aemeath_echo_sigillum_hit_1",
        "aemeath_echo_sigillum_hit_2",
    ]
    assert [effect.metadata["relative_due_frames"] for effect in sigillum_effects] == [25.0, 55.0]
    if previous_effect_instance_id is not None:
        previous = next(effect for effect in sim.state.scheduled_effects if effect.instance_id == previous_effect_instance_id)
        assert_close(previous.remaining_duration, 10.0, "pre-existing remaining duration")
        assert_close(previous.time_until_next_tick, 0.75, "pre-existing phase")


def test_sync_strike_window_survives_sigillum() -> None:
    sim = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="aemeath")
    assert sim.execute_action("aemeath_basic_form_stage_2")
    assert aemeath_state(sim)["sync_strike_window_type"] == "armament_merge"
    assert aemeath_state(sim)["sync_strike_window_remaining"] == 1

    sim.schedule_effect(
        instance_id="test:preexisting:phase",
        effect_id="test_preexisting_phase_guard",
        source_character_id="mornye",
        source_action_id="test_preexisting",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=10.0,
        tick_interval=1.0,
        time_until_next_tick=0.75,
        source_status="test_preexisting_phase_guard",
    )
    before_state = copy.deepcopy(aemeath_state(sim))
    before_time = (sim.state.current_time, sim.state.combat_time)

    assert sim.execute_action("aemeath_echo_sigillum")
    assert aemeath_state(sim) == before_state
    assert (sim.state.current_time, sim.state.combat_time) == before_time
    assert_sigillum_auxiliary_side_effects(sim, previous_effect_instance_id="test:preexisting:phase")

    assert sim.resolve_action(sim.actions["aemeath_resonance_skill"]).id == "aemeath_sync_strike_armament_merge"
    assert sim.execute_action("aemeath_resonance_skill")
    assert sim.timeline[-1].resolved_action_id == "aemeath_sync_strike_armament_merge"


def test_overdrive_form_switch_window_survives_sigillum() -> None:
    sim = Simulation.from_json("data", selected_character_ids=PARTY_ID, initial_active_character="aemeath")
    data = aemeath_state(sim)
    data["form"] = "mech"
    data["overdrive_form_switch_window_remaining"] = 1
    before_state = copy.deepcopy(data)
    before_time = (sim.state.current_time, sim.state.combat_time)

    assert sim.execute_action("aemeath_echo_sigillum")
    assert aemeath_state(sim) == before_state
    assert (sim.state.current_time, sim.state.combat_time) == before_time
    assert aemeath_state(sim)["overdrive_form_switch_window_remaining"] == 1
    assert_sigillum_auxiliary_side_effects(sim)


def main() -> None:
    test_sync_strike_window_survives_sigillum()
    test_overdrive_form_switch_window_survives_sigillum()
    print("aemeath_sigillum_auxiliary_state_isolation_smoke_test ok")


if __name__ == "__main__":
    main()
