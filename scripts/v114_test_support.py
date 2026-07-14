from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.models import ActionData
from simulator.simulation import Simulation


PARTY = "aemeath_mornye_lynae_enabled_test_party"
OUTRO_BUFF_ID = "aemeath_outro_unseen_guard_all_damage_amp"


def build(*, party: str = PARTY, active: str = "aemeath") -> Simulation:
    return Simulation.from_json(ROOT / "data", party=party, initial_active_character=active)


def set_concerto(sim: Simulation, character_id: str, value: float = 100.0) -> None:
    sim.state.concerto_energy[character_id] = value
    state = sim.state.character_mechanics_state.setdefault(character_id, {})
    state["concerto_energy"] = value
    state["concerto_energy_cap"] = 100.0
    state["concerto_ready"] = value >= 100.0


def add_wait(sim: Simulation, seconds: float, action_id: str = "v114_test_wait") -> str:
    sim.actions[action_id] = ActionData(
        id=action_id,
        name=f"V114 test wait {seconds}",
        character_id=None,
        action_type="wait",
        duration=seconds,
        action_time=seconds,
        combat_time_cost=seconds,
        cooldown=0.0,
        resonance_energy_cost=0.0,
        policy_selectable=False,
        mechanic_effects={"skip_character_after_action": True},
        data_status="v114_test_fixture",
    )
    return action_id


def add_event_action(
    sim: Simulation,
    character_id: str,
    event_tag: str,
    *,
    seconds: float = 0.5,
) -> str:
    action_id = f"v114_test_{character_id}_{event_tag}"
    sim.actions[action_id] = ActionData(
        id=action_id,
        name=f"V114 {character_id} {event_tag}",
        character_id=character_id,
        action_type="basic_attack",
        duration=seconds,
        action_time=seconds,
        combat_time_cost=seconds,
        cooldown=0.0,
        damage_multiplier=0.1,
        resonance_energy_cost=0.0,
        mechanic_event_tags=[event_tag],
        tags=[character_id, "v114_test_fixture"],
        policy_selectable=False,
        data_status="v114_test_fixture",
    )
    return action_id


def outro_instances(sim: Simulation) -> dict[str, object]:
    return {
        active.target_character_id: active
        for active in sim.state.active_buffs
        if active.buff_id == OUTRO_BUFF_ID and active.remaining_duration > 0.0
    }


def value(active: object) -> float:
    return float(active.metadata.get("dynamic_value", 0.0))


def assert_close(actual: float, expected: float, tolerance: float = 1e-9) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), (actual, expected)

