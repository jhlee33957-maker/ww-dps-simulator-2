from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from characters.aemeath import AemeathMechanic
from simulator.models import CombatState


def main() -> None:
    state = CombatState(active_character_id="aemeath", party_members=["aemeath"])
    mechanic = AemeathMechanic()
    mechanic.initialize_state(state)
    context = {
        "tune_break_event_id": "guard:aemeath_starburst:1",
        "host_action_id": "guard_tune_break",
        "response_id": "aemeath_starburst",
        "source_character_id": "aemeath",
        "interfered_state": "tune_rupture_interfered",
        "triggered": True,
        "response_damage": 1.0,
    }
    state.mechanics_config = {"aemeath": {"aemeath_resonance_mode": "tune_rupture"}}
    event = mechanic.on_party_tune_response_resolved(state, context)
    assert event is not None
    assert state.rupturous_trail_stacks == 10
    assert state.rupturous_trail_remaining == 30.0
    assert "rupturous_trail_stacks" not in state.character_mechanics_state["aemeath"]
    assert "rupturous_trail_remaining" not in state.character_mechanics_state["aemeath"]
    assert event["source_status"] == "workbook_confirmed_c0"
    assert event["source_ref"] == "角色-女!2844"
    assert event["event_type"] == "rupturous_trail_gain"
    assert event["response_source_character_id"] == "aemeath"
    assert event["response_action_id"] == "aemeath_starburst"
    assert event["stacks_before"] == 0
    assert event["requested_gain"] == 10
    assert event["applied_gain"] == 10
    assert event["stacks_after"] == 10
    assert event["remaining_after"] == 30.0
    print("aemeath_rupturous_trail_runtime_guard_smoke_test ok")


if __name__ == "__main__":
    main()
