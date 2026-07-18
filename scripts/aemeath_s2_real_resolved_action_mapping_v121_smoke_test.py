from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim
from simulator.account_constellation_effects import AEMEATH_S2_ENHANCED_SKILL_IDS


def _first_account_context(result):
    return [
        event
        for hit in result.hit_details
        for event in hit.get("account_constellation_damage_context", [])
    ]


def main() -> None:
    assert AEMEATH_S2_ENHANCED_SKILL_IDS == {
        "aemeath_sync_strike_armament_merge",
        "aemeath_sync_strike_call_of_dawn",
    }
    for action_id in sorted(AEMEATH_S2_ENHANCED_SKILL_IDS):
        sim = make_account_sim("aemeath")
        sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
        assert sim.execute_action(action_id)
        context = _first_account_context(sim.last_action_result)
        event = next(event for event in context if event["event_type"] == "aemeath_s2_direct_enhanced_skill_coefficient")
        assert event["coefficient_multiplier"] == 2.0
        sequence = [
            event
            for event in context
            if event["event_type"] == "aemeath_s2_tune_stack_generated_hit"
        ]
        assert len(sequence) == 5
        event = sequence[0]
        assert event["stacks_before"] == 0
        assert event["stacks_after"] == 1
        assert event["damage_amp_add"] == 0.0

    sim = make_account_sim("aemeath")
    assert sim.execute_action("aemeath_form_switch_to_mech_normal")
    assert not [
        event
        for event in _first_account_context(sim.last_action_result)
        if event["event_type"] == "aemeath_s2_tune_stack_generated_hit"
    ]
    print("aemeath_s2_real_resolved_action_mapping_v121_smoke_test ok")


if __name__ == "__main__":
    main()
