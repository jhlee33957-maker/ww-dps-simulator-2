from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim
from simulator.account_constellation_effects import ACCOUNT_AEMEATH_S4_BUFF_ID


def main() -> None:
    sim = make_account_sim("aemeath")
    assert sim.execute_action("aemeath_form_switch_to_mech_normal")
    trigger = sim.last_action_result
    assert ACCOUNT_AEMEATH_S4_BUFF_ID in trigger.hit_details[0]["active_buff_ids"]
    assert trigger.hit_details[0]["all_dmg_bonus"] >= 0.2
    assert any(event["event_type"] == "aemeath_s4_party_buff_confirmed" for event in trigger.account_constellation_events)
    assert sim.state.character_mechanics_state["_account_constellation"]["aemeath_s4_remaining"] > 0.0

    assert sim.execute_action("aemeath_basic_form_stage_1")
    followup = sim.last_action_result.hit_details[0]
    assert ACCOUNT_AEMEATH_S4_BUFF_ID in followup["active_buff_ids"]
    assert followup["all_dmg_bonus"] >= 0.2
    print("aemeath_s4_real_trigger_and_damage_v121_smoke_test ok")


if __name__ == "__main__":
    main()
