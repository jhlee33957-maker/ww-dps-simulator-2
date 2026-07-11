from __future__ import annotations

import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.resource_system import sync_concerto_state
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_qte_sim() -> Simulation:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config["concerto_transition"]["qte_mode"] = "enabled"
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="aemeath", transition_config=config)
    state = sync_concerto_state(sim.state, "aemeath")
    state["concerto_energy"] = 100.0
    state["concerto_ready"] = True
    sim.state.concerto_energy["aemeath"] = 100.0
    return sim


def main() -> None:
    sim = make_qte_sim()
    assert sim.execute_action("swap_to_mornye")
    intro = sim.timeline[-1]
    assert intro.resolved_action_id == "transition:mornye_intro_convergence"
    activation_time = intro.combat_time_end

    damage_1 = sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye")
    damage_2 = sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_2:mornye")
    assert damage_1 is not None
    assert damage_2 is None
    assert_close(damage_1.activation_combat_time, activation_time, "Intro activation approximation")
    assert "activation_timing_approximation_action_end" in damage_1.metadata["activation_timing_status"]

    while sim.scheduled_effect_by_instance_id("mornye_syntony_field_damage_1:mornye") is not None:
        assert sim.execute_action("mornye_basic_attack")

    events = list(sim.state.scheduled_effect_event_log)
    assert [event["payload_action_id"] for event in events] == ["mornye_syntony_field_damage"] * 5
    assert [round((event["combat_time"] - activation_time) * 60) for event in events] == [1, 28, 55, 82, 109]
    assert_close(sum(float(event.get("off_tune_value", 0.0)) for event in events), 0.0, "Intro raw Off-Tune")
    assert_close(sum(float(event.get("off_tune_gain", 0.0)) for event in events), 0.0, "Intro applied Off-Tune")
    assert_close(sum(float(event.get("base_resonance_energy_gain", 0.0)) for event in events), 0.0, "Intro base RE")
    assert_close(sum(float(event.get("concerto_energy_gained", 0.0)) for event in events), 0.0, "Intro CE")
    assert all(event["scheduled_resource_policy"] == "none" for event in events)

    print("mornye_syntony_field_intro_qte_smoke_test ok")


if __name__ == "__main__":
    main()
