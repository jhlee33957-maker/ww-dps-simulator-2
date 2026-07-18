from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_lynae_visual_impact
from simulator.account_constellation_effects import ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID


def main() -> None:
    sim = make_account_sim("lynae")
    ready_lynae_visual_impact(sim)
    assert sim.execute_action("lynae_visual_impact")
    first_hit = sim.last_action_result.hit_details[0]
    assert first_hit["account_damage_amp_add"] == 0.25
    assert any(
        event["event_type"] == "lynae_s2_self_deepen_formula"
        for event in first_hit["account_constellation_damage_context"]
    )

    sim = make_account_sim("lynae")
    assert sim.execute_action("swap_to_aemeath")
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert account["lynae_s2_outro_target"] == "aemeath"
    assert account["lynae_s2_outro_remaining"] == 14.0
    assert ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID in {buff.buff_id for buff in sim.state.active_buffs}

    assert sim.execute_action("swap_to_mornye")
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert account["lynae_s2_outro_target"] is None
    assert account["lynae_s2_outro_remaining"] == 0.0
    assert ACCOUNT_LYNAE_S2_OUTRO_BUFF_ID not in {buff.buff_id for buff in sim.state.active_buffs}
    print("lynae_s2_first_action_and_outro_exact_v121_smoke_test ok")


if __name__ == "__main__":
    main()
