from __future__ import annotations

import copy
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
PAYLOAD_ID = "mornye_syntony_field_damage"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def make_sim(*, initial_active: str = "mornye", stat_overrides: dict | None = None) -> Simulation:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    return Simulation.from_json(
        DATA_DIR,
        party=PARTY_ID,
        initial_active_character=initial_active,
        transition_config=config,
        stat_overrides=stat_overrides,
    )


def schedule_mornye_fixture(
    sim: Simulation,
    *,
    instance_id: str = "sched:mornye:field",
    payload_action_id: str = PAYLOAD_ID,
    remaining_duration: float = 8.0,
    tick_interval: float = 2.0,
    time_until_next_tick: float = 1.0,
    refresh_rule: str = "replace",
    metadata: dict | None = None,
    max_trigger_count: int | None = None,
):
    return sim.schedule_effect(
        instance_id=instance_id,
        effect_id="test_mornye_field_scheduler_fixture",
        source_character_id="mornye",
        source_action_id="scheduler_fixture_source",
        payload_action_id=payload_action_id,
        remaining_duration=remaining_duration,
        tick_interval=tick_interval,
        time_until_next_tick=time_until_next_tick,
        refresh_rule=refresh_rule,
        max_trigger_count=max_trigger_count,
        source_status="scheduler_test_fixture",
        source_ref="scripts/scheduled_effect_*_smoke_test.py",
        metadata=metadata or {},
    )


def execute_aemeath_zero_combat_liberation(sim: Simulation):
    sim.state.active_character_id = "aemeath"
    sim.state.resonance_energy["aemeath"] = sim.characters["aemeath"].resonance_energy_max
    assert sim.execute_action("aemeath_resonance_liberation")
    return sim.timeline[-1]


def execute_mornye_host(sim: Simulation, action_id: str = "mornye_basic_attack"):
    sim.state.active_character_id = "mornye"
    assert sim.execute_action(action_id)
    return sim.timeline[-1]


def snapshot_player_side_effect_state(sim: Simulation, source_character_id: str = "mornye") -> dict:
    return {
        "active_character_id": sim.state.active_character_id,
        "current_time": sim.state.current_time,
        "combat_time": sim.state.combat_time,
        "resonance_energy": sim.state.resonance_energy.get(source_character_id),
        "concerto_energy": sim.state.concerto_energy.get(source_character_id),
        "character_state": copy.deepcopy(sim.state.character_states.get(source_character_id, {})),
        "cooldowns": copy.deepcopy(sim.state.cooldowns),
        "weapon_effect_cooldowns": copy.deepcopy(sim.state.weapon_effect_cooldowns),
    }
