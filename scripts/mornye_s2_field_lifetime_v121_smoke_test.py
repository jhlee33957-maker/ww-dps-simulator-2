from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim
from simulator.buff_system import support_stat_context


def main() -> None:
    sim = make_account_sim("mornye")
    assert sim.execute_action("mornye_heavy_geopotential_shift")
    context = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert context["runtime_off_tune_buildup_rate_bonus"] == 0.7
    assert context["current_off_tune_buildup_rate"] == 1.7
    assert context["c2_off_tune_bonus_active"] is True
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert account["mornye_s2_field_remaining"] == 25.0

    assert sim.execute_action("short_wait")
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert 0.0 < account["mornye_s2_field_remaining"] < 25.0
    context = support_stat_context(sim.characters["mornye"], sim.state, sim.buffs)
    assert context["current_off_tune_buildup_rate"] == 1.7
    print("mornye_s2_field_lifetime_v121_smoke_test ok")


if __name__ == "__main__":
    main()
