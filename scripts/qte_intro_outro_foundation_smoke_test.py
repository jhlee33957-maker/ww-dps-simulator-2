from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.v114_test_support import OUTRO_BUFF_ID, assert_close, build, outro_instances, set_concerto, value
from simulator.party_transition import GENERIC_SWAP_SOURCE_STATUS, swap_reentry_key


def main() -> None:
    configured = build()
    outro = configured.transition_config["characters"]["aemeath"]["outro"]
    assert outro["enabled"] is True
    assert outro["implementation_status"] == "implemented_v114"
    assert outro["action_id"] == "aemeath_outro_unseen_guard"
    assert_close(outro["action_time"], 0.0)
    assert_close(outro["combat_time_cost"], 0.0)
    assert outro["requires_concerto"] is True
    assert outro["consume_concerto_on_apply"] is True

    for target in ("aemeath", "mornye", "lynae"):
        action = configured.actions[f"swap_to_{target}"]
        assert_close(action.action_time or 0.0, 0.0)
        assert_close(action.combat_time_cost or 0.0, 0.0)
        assert_close(action.cooldown, 1.0)
        assert action.cooldown_group == swap_reentry_key(target)
        assert action.mechanic_effects["zero_time_transition_action"] is True

    normal = build()
    assert normal.execute_action("swap_to_mornye")
    row = normal.timeline[-1]
    assert row.outgoing_character_id == "aemeath"
    assert row.incoming_character_id == "mornye"
    assert row.transition_type == "normal_swap"
    assert row.transition_reason == "concerto_not_ready"
    assert_close(row.action_time, 0.0)
    assert_close(row.combat_time_cost, 0.0)
    assert row.swap_timing_is_placeholder is False
    assert row.generic_swap_zero_time is True
    assert row.swap_contract_source_status == GENERIC_SWAP_SOURCE_STATUS
    assert row.transition_warnings == []
    assert row.transition_events == []
    assert row.aemeath_outro_applied is False
    assert row.outgoing_outro_applied is False
    assert row.outgoing_concerto_consumed is False
    assert_close(normal.state.concerto_energy["aemeath"], 0.0)
    assert_close(normal.state.cooldowns[swap_reentry_key("aemeath")], 1.0)

    full = build()
    set_concerto(full, "aemeath")
    assert full.execute_action("swap_to_mornye")
    row = full.timeline[-1]
    base_events = [
        event for event in row.transition_events if event.get("action_id") == "aemeath_outro_unseen_guard"
    ]
    assert row.transition_type == "full_concerto_transition"
    assert row.aemeath_outro_applied is True
    assert row.outgoing_outro_applied is True
    assert row.outgoing_concerto_consumed is True
    assert_close(row.outgoing_concerto_before, 100.0)
    assert_close(row.outgoing_concerto_after, 0.0)
    assert_close(full.state.concerto_energy["aemeath"], 0.0)
    assert len(base_events) == 1
    assert base_events[0]["consume_concerto_on_apply"] is True
    instances = outro_instances(full)
    assert set(instances) == {"mornye", "lynae"}
    assert "aemeath" not in instances
    assert all(active.buff_id == OUTRO_BUFF_ID for active in instances.values())
    assert all(value(active) == 0.1 for active in instances.values())

    print("qte_intro_outro_foundation_smoke_test: PASS")


if __name__ == "__main__":
    main()
