from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lynae_real_cycle_concerto_smoke_test import MORNYE_OPENER
from scripts.v114_test_support import set_concerto
from search.mcts_state import create_initial_simulation, policy_action_ids
from search.search_state_codec import (
    DIAGNOSTIC_ONLY_FIELDS,
    clear_search_diagnostics,
    clone_simulation_for_search,
    compact_combat_state_payload,
    execute_action_for_search,
    full_node_state_fingerprint,
    future_state_fingerprint,
)


def _base(*, active: str = "aemeath"):
    simulation = create_initial_simulation(combat_duration=120.0)
    if active != "aemeath":
        assert execute_action_for_search(simulation, f"swap_to_{active}")
    return simulation


def _states():
    initial = _base()

    sigillum = _base()
    assert execute_action_for_search(sigillum, "aemeath_echo_sigillum")
    assert sigillum.state.scheduled_effects

    outro = _base()
    set_concerto(outro, "aemeath")

    mornye = _base(active="mornye")
    for action_id in MORNYE_OPENER:
        assert execute_action_for_search(mornye, action_id), action_id
    mornye_state = mornye.state.character_mechanics_state["mornye"]
    assert float(mornye_state.get("syntony_field_remaining", 0.0)) > 0.0 or float(
        mornye_state.get("high_syntony_field_remaining", 0.0)
    ) > 0.0

    tune_break = _base()
    tune_break.state.enemy_off_tune_current = tune_break.state.enemy_off_tune_max
    tune_break.state.enemy_mistune_active = True
    tune_break.state.enemy_tune_break_available = True
    tune_break.state.enemy_tune_break_cooldown_remaining = 0.0

    horizon = _base()
    horizon.state.combat_time = 119.95
    horizon.state.current_time = 119.95

    return {
        "initial_zero_time_swap": initial,
        "scheduled_sigillum": sigillum,
        "timed_intro_aemeath_outro": outro,
        "mornye_field": mornye,
        "tune_break": tune_break,
        "horizon_truncation": horizon,
    }


def _assert_diagnostic_only_difference(full, light) -> None:
    full_raw = full.state.model_dump(mode="json")
    light_raw = light.state.model_dump(mode="json")
    differing = {name for name in full_raw if full_raw[name] != light_raw[name]}
    assert differing <= DIAGNOSTIC_ONLY_FIELDS, differing
    for name in DIAGNOSTIC_ONLY_FIELDS:
        value = getattr(light.state, name)
        if isinstance(value, (list, dict, set)):
            assert not value, (name, len(value))
    assert light.timeline == []


def main() -> None:
    checked = 0
    labels_with_action: dict[str, list[str]] = {}
    for label, source in _states().items():
        actions = policy_action_ids(source)
        legal = [action_id for action_id in actions if action_id in source.valid_action_ids()]
        assert legal, label
        labels_with_action[label] = legal
        for action_id in legal:
            full = clone_simulation_for_search(source)
            light = clone_simulation_for_search(source)
            full_ok = bool(full.execute_action(action_id))
            light_ok = execute_action_for_search(light, action_id)
            assert full_ok == light_ok is True, (label, action_id)
            full_result = full.last_action_result
            light_result = light.last_action_result
            assert full_result is not None and light_result is not None
            assert full_result.selected_action_id == light_result.selected_action_id == action_id
            assert full_result.resolved_action_id == light_result.resolved_action_id
            assert compact_combat_state_payload(full.state, include_objective=True) == compact_combat_state_payload(
                light.state, include_objective=True
            ), (label, action_id)
            assert future_state_fingerprint(full) == future_state_fingerprint(light)
            assert full_node_state_fingerprint(full) == full_node_state_fingerprint(light)
            assert full.valid_action_ids() == light.valid_action_ids()
            _assert_diagnostic_only_difference(full, light)
            checked += 1

    assert "aemeath_echo_sigillum" in labels_with_action["initial_zero_time_swap"]
    assert any(action.startswith("swap_to_") for action in labels_with_action["initial_zero_time_swap"])
    assert "swap_to_lynae" in labels_with_action["timed_intro_aemeath_outro"]
    assert "aemeath_tune_break" in labels_with_action["tune_break"]
    assert "short_wait" in labels_with_action["scheduled_sigillum"]
    assert "short_wait" in labels_with_action["horizon_truncation"]
    print(f"mcts_lightweight_action_execution_parity_smoke_test ok states={len(labels_with_action)} actions={checked}")


if __name__ == "__main__":
    main()
