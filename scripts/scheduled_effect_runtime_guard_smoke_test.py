from __future__ import annotations

import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.observation_features import OBSERVATION_VERSION, build_observation_labels
from env.wuwa_env import WuwaDpsEnv
from simulator import scheduled_effects
from simulator.action_executor import execute_scheduled_damage_event
from simulator.models import CombatState
from simulator.simulation import Simulation
from scheduled_effect_test_helpers import make_sim


def main() -> None:
    scheduler_source = inspect.getsource(scheduled_effects.advance_scheduled_effects)
    assert "combat_elapsed" in scheduler_source
    assert "action_time" not in scheduler_source
    assert "current_time" not in scheduler_source
    assert "activation_combat_time" in scheduler_source
    assert "trigger_on_apply_pending" in scheduler_source
    assert "triggers <= 0" in scheduler_source
    assert "starting_phase - active_elapsed + triggers * float(effect.tick_interval)" in scheduler_source

    scheduled_damage_source = inspect.getsource(execute_scheduled_damage_event)
    assert ".execute_action(" not in scheduled_damage_source
    assert "apply_resource_changes" not in scheduled_damage_source
    assert "cooldowns[" not in scheduled_damage_source
    assert 'model_copy(update={"character_id": effect.source_character_id})' in scheduled_damage_source
    assert "policy_selectable" not in scheduled_damage_source

    schedule_source = inspect.getsource(scheduled_effects.schedule_effect)
    assert 'refresh_rule == "refresh_duration"' in schedule_source
    assert 'refresh_rule == "keep_existing"' in schedule_source
    assert '"immediate_trigger_pending": False' in schedule_source
    assert "trigger_on_apply_pending=bool(trigger_on_apply)" in schedule_source

    simulation_schedule_source = inspect.getsource(Simulation.schedule_effect)
    assert 'result.get("operation") in {"created", "replaced"}' in simulation_schedule_source

    for relative in ("characters/mornye.py", "characters/lynae.py"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert ".schedule_effect(" not in source
        assert "schedule_effect(" not in source

    sim = make_sim()
    assert sim.scheduled_effect_by_instance_id("missing") is None
    assert all(action.policy_selectable is False for action in [sim.actions["mornye_syntony_field_damage"]])
    assert "mornye_syntony_field_damage" not in sim.get_policy_action_ids()

    created = sim.schedule_effect(
        instance_id="guard:activation",
        effect_id="guard",
        source_character_id="mornye",
        source_action_id="guard",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=2.0,
        time_until_next_tick=1.0,
        activation_combat_time=5.0,
        trigger_on_apply=True,
        source_status="guard",
    )
    assert created["operation"] == "created"
    assert created["immediate_trigger_pending"] is True
    effect = sim.scheduled_effect_by_instance_id("guard:activation")
    assert effect.activation_combat_time == 5.0
    assert effect.trigger_on_apply_pending is True
    restored = CombatState.model_validate(sim.state.model_dump(mode="json"))
    assert restored.scheduled_effects[0].activation_combat_time == 5.0
    assert restored.scheduled_effects[0].trigger_on_apply_pending is True

    before = effect.model_dump(mode="json")
    sim.execute_action("short_wait")
    assert sim.timeline[-1].scheduled_damage_events == []
    after = sim.scheduled_effect_by_instance_id("guard:activation").model_dump(mode="json")
    assert after == before

    refreshed = sim.schedule_effect(
        instance_id="guard:activation",
        effect_id="guard",
        source_character_id="mornye",
        source_action_id="guard",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=9.0,
        tick_interval=2.0,
        activation_combat_time=0.0,
        refresh_rule="refresh_duration",
        trigger_on_apply=True,
        source_status="guard",
    )
    assert refreshed["operation"] == "refreshed"
    assert refreshed["immediate_trigger_pending"] is False
    assert refreshed["immediate_trigger_executed"] is False

    kept = sim.schedule_effect(
        instance_id="guard:activation",
        effect_id="guard",
        source_character_id="mornye",
        source_action_id="guard",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=10.0,
        tick_interval=1.0,
        activation_combat_time=0.0,
        refresh_rule="keep_existing",
        trigger_on_apply=True,
        source_status="guard",
    )
    assert kept["operation"] == "kept_existing"
    assert kept["immediate_trigger_pending"] is False
    assert kept["immediate_trigger_executed"] is False

    boundary = make_sim()
    boundary.state.combat_time = 10.0
    boundary.schedule_effect(
        instance_id="guard:boundary",
        effect_id="guard",
        source_character_id="mornye",
        source_action_id="guard",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=2.0,
        time_until_next_tick=0.0,
        activation_combat_time=10.5,
        source_status="guard",
    )
    assert boundary.execute_action("short_wait")
    effect = boundary.scheduled_effect_by_instance_id("guard:boundary")
    assert len(boundary.timeline[-1].scheduled_damage_events) == 1
    assert effect.trigger_count == 1
    assert effect.time_until_next_tick == 2.0
    assert boundary.execute_action("short_wait")
    assert boundary.timeline[-1].scheduled_damage_events == []

    boundary_apply = make_sim()
    boundary_apply.state.combat_time = 20.0
    boundary_apply.schedule_effect(
        instance_id="guard:boundary_apply",
        effect_id="guard",
        source_character_id="mornye",
        source_action_id="guard",
        payload_action_id="mornye_syntony_field_damage",
        remaining_duration=8.0,
        tick_interval=1.0,
        time_until_next_tick=0.0,
        activation_combat_time=20.5,
        trigger_on_apply=True,
        source_status="guard",
    )
    assert boundary_apply.execute_action("short_wait")
    assert [event["scheduled_effect_trigger_kind"] for event in boundary_apply.timeline[-1].scheduled_damage_events] == [
        "trigger_on_apply"
    ]

    env = WuwaDpsEnv(data_dir="data", party="aemeath_mornye_lynae_enabled_test_party")
    obs, _info = env.reset()
    assert OBSERVATION_VERSION == "slot_generic_mechanics_v4"
    assert len(obs) == 312
    assert len(build_observation_labels()) == 312
    print("scheduled_effect_runtime_guard_smoke_test ok")


if __name__ == "__main__":
    main()
