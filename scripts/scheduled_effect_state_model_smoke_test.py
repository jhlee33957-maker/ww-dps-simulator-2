from __future__ import annotations

import copy

from scheduled_effect_test_helpers import PAYLOAD_ID, assert_close, make_sim, schedule_mornye_fixture
from simulator.models import CombatState


def expect_value_error(fn, label: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(f"{label} did not fail clearly")


def main() -> None:
    sim = make_sim()
    result = schedule_mornye_fixture(sim, metadata={"phase": "initial"})
    assert result["status"] == "scheduled"
    assert len(sim.state.scheduled_effects) == 1
    effect = sim.state.scheduled_effects[0]
    assert effect.instance_id == "sched:mornye:field"
    assert effect.effect_id == "test_mornye_field_scheduler_fixture"
    assert effect.source_character_id == "mornye"
    assert effect.source_action_id == "scheduler_fixture_source"
    assert effect.payload_action_id == PAYLOAD_ID
    assert_close(effect.remaining_duration, 8.0, "duration")
    assert_close(effect.tick_interval, 2.0, "interval")
    assert_close(effect.time_until_next_tick, 1.0, "phase")
    assert effect.trigger_count == 0
    assert effect.max_trigger_count is None
    assert effect.refresh_rule == "replace"
    assert effect.source_status == "scheduler_test_fixture"
    assert effect.source_ref
    assert effect.metadata == {"phase": "initial"}

    restored = CombatState.model_validate(sim.state.model_dump(mode="json"))
    assert restored.scheduled_effects[0].model_dump(mode="json") == effect.model_dump(mode="json")

    copied = copy.deepcopy(sim.state)
    copied.scheduled_effects[0].remaining_duration = 3.0
    assert_close(sim.state.scheduled_effects[0].remaining_duration, 8.0, "deep copy independence")

    reset = make_sim()
    assert reset.state.scheduled_effects == []

    expect_value_error(
        lambda: sim.schedule_effect(
            instance_id="bad-interval",
            effect_id="bad",
            source_character_id="mornye",
            payload_action_id=PAYLOAD_ID,
            remaining_duration=1.0,
            tick_interval=0.0,
            source_status="test",
        ),
        "invalid interval",
    )
    expect_value_error(
        lambda: sim.schedule_effect(
            instance_id="bad-payload",
            effect_id="bad",
            source_character_id="mornye",
            payload_action_id="does_not_exist",
            remaining_duration=1.0,
            tick_interval=1.0,
            source_status="test",
        ),
        "unknown payload",
    )
    expect_value_error(
        lambda: sim.schedule_effect(
            instance_id="policy-payload",
            effect_id="bad",
            source_character_id="mornye",
            payload_action_id="mornye_basic_attack",
            remaining_duration=1.0,
            tick_interval=1.0,
            source_status="test",
        ),
        "policy payload",
    )
    print("scheduled_effect_state_model_smoke_test ok")


if __name__ == "__main__":
    main()
