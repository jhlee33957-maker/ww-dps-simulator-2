from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.mcts_reporting import replay_completed_route
from search.mcts_state import create_initial_simulation, policy_action_ids
from search.search_state_codec import (
    DIAGNOSTIC_ONLY_FIELDS,
    compact_combat_state_payload,
    execute_action_for_search,
    full_node_state_fingerprint,
    future_state_fingerprint,
    sequence_sha256,
)


def _assert_equal(full, light) -> None:
    assert compact_combat_state_payload(full.state, include_objective=True) == compact_combat_state_payload(
        light.state, include_objective=True
    )
    assert future_state_fingerprint(full) == future_state_fingerprint(light)
    assert full_node_state_fingerprint(full) == full_node_state_fingerprint(light)
    assert full.valid_action_ids() == light.valid_action_ids()


def _run(duration: float) -> tuple[list[str], list[str], object, object]:
    full = create_initial_simulation(combat_duration=duration)
    light = create_initial_simulation(combat_duration=duration)
    action_ids = policy_action_ids(full)
    selected: list[str] = []
    resolved: list[str] = []
    zero_tail = 0
    step = 0
    while full.state.combat_time < duration - 1e-9:
        full_legal = [action for action in action_ids if action in full.valid_action_ids()]
        light_legal = [action for action in action_ids if action in light.valid_action_ids()]
        assert full_legal == light_legal and full_legal
        if step == 0 and "aemeath_echo_sigillum" in full_legal:
            action_id = "aemeath_echo_sigillum"
        elif zero_tail >= 2 and "short_wait" in full_legal:
            action_id = "short_wait"
        else:
            action_id = full_legal[(step * 7 + 3) % len(full_legal)]
        before = float(full.state.combat_time)
        assert full.execute_action(action_id)
        assert execute_action_for_search(light, action_id)
        assert full.last_action_result is not None and light.last_action_result is not None
        assert full.last_action_result.resolved_action_id == light.last_action_result.resolved_action_id
        selected.append(action_id)
        resolved.append(str(full.last_action_result.resolved_action_id))
        _assert_equal(full, light)
        zero_tail = zero_tail + 1 if full.state.combat_time <= before + 1e-12 else 0
        step += 1
        assert step <= 512
    return selected, resolved, full, light


def main() -> None:
    short_selected, short_resolved, short_full, short_light = _run(8.0)
    selected, resolved, full, light = _run(120.0)
    assert short_full.state.combat_time == short_light.state.combat_time == 8.0
    assert full.state.combat_time == light.state.combat_time == 120.0
    assert full.state.total_damage == light.state.total_damage
    assert len(selected) <= 512
    for name in DIAGNOSTIC_ONLY_FIELDS:
        value = getattr(light.state, name)
        if isinstance(value, (list, dict, set)):
            assert not value, name
    assert light.timeline == []

    route = {
        "route_id": "lightweight_rollout_parity_fixture",
        "selected_sequence": selected,
        "resolved_sequence": resolved,
        "selected_sequence_sha256": sequence_sha256(selected),
        "resolved_sequence_sha256": sequence_sha256(resolved),
        "total_damage": float(full.state.total_damage),
    }
    replay = replay_completed_route(route)
    assert replay["selected_sequence_sha256"] == route["selected_sequence_sha256"]
    assert replay["resolved_sequence_sha256"] == route["resolved_sequence_sha256"]
    assert replay["total_damage"] == route["total_damage"]
    assert sequence_sha256(short_selected) and sequence_sha256(short_resolved)
    print(
        "mcts_lightweight_rollout_state_parity_smoke_test ok "
        f"short_actions={len(short_selected)} full_actions={len(selected)} damage={full.state.total_damage}"
    )


if __name__ == "__main__":
    main()
