from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import (  # noqa: E402
    assert_search_state_invariants,
    future_state_payload,
    restore_simulation_from_state,
    serialize_simulation_state,
)
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    route = json.loads((ROOT / "data" / "manual_120s_baseline_routes_v104.json").read_text(encoding="utf-8-sig"))
    selected_actions = route["routes"]["primary"]["selected_policy_actions"]
    normal = _sim()
    restored_each_step = _sim()
    for index, action_id in enumerate(selected_actions):
        assert action_id in normal.valid_action_ids(), (index, action_id, normal.valid_action_ids())
        payload = serialize_simulation_state(restored_each_step)
        restored_each_step = restore_simulation_from_state(restored_each_step, payload)
        assert_search_state_invariants(restored_each_step.state)
        assert restored_each_step.state.character_states is restored_each_step.state.character_mechanics_state
        assert normal.valid_action_ids() == restored_each_step.valid_action_ids(), index
        assert action_id in restored_each_step.valid_action_ids(), (index, action_id, restored_each_step.valid_action_ids())
        assert normal.execute_action(action_id), index
        assert restored_each_step.execute_action(action_id), index
        normal_action = normal.timeline[-1]
        restored_action = restored_each_step.timeline[-1]
        assert normal_action.resolved_action_id == restored_action.resolved_action_id, (index, normal_action.resolved_action_id, restored_action.resolved_action_id)
        if index == 27:
            assert normal_action.resolved_action_id == "transition:aemeath_qte_intro_mech"
        _assert_close(normal.state.total_damage, restored_each_step.state.total_damage, index)
        _assert_close(normal.state.combat_time, restored_each_step.state.combat_time, index)
        _assert_close(normal.state.current_time, restored_each_step.state.current_time, index)
        assert normal.state.active_character_id == restored_each_step.state.active_character_id, index
        assert normal.state.resonance_energy == restored_each_step.state.resonance_energy, index
        assert normal.state.concerto_energy == restored_each_step.state.concerto_energy, index
        assert normal.state.cooldowns == restored_each_step.state.cooldowns, index
        assert normal.state.active_buffs == restored_each_step.state.active_buffs, index
        assert normal.state.team_buffs == restored_each_step.state.team_buffs, index
        assert normal.state.scheduled_effects == restored_each_step.state.scheduled_effects, index
        assert future_state_payload(normal) == future_state_payload(restored_each_step), index
    print("beam_search_clone_behavioral_parity_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


def _assert_close(actual: float, expected: float, index: int) -> None:
    assert abs(float(actual) - float(expected)) <= 1e-9, (index, actual, expected)


if __name__ == "__main__":
    main()
