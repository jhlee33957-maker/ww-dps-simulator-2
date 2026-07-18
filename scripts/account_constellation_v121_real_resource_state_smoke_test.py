from __future__ import annotations

from account_constellation_v121_runtime_test_utils import (
    event_types,
    make_account_sim,
    ready_aemeath_charged_ii,
    ready_mornye_distributed_array,
)


def main() -> None:
    aemeath = make_account_sim("aemeath")
    ready_aemeath_charged_ii(aemeath)
    assert aemeath.execute_action("aemeath_heavy_aemeath_charged_2")
    assert aemeath.state.character_mechanics_state["aemeath"]["synchronization_rate"] == 100.0

    lynae = make_account_sim("lynae", precombat=2.01)
    assert lynae.state.character_mechanics_state["lynae"]["overflow"] == 120.0
    assert lynae.state.character_mechanics_state["_account_constellation"]["lynae_precombat_overflow_restored"] == 120.0

    mornye = make_account_sim("mornye")
    ready_mornye_distributed_array(mornye)
    assert mornye.execute_action("mornye_skill_distributed_array")
    result = mornye.last_action_result
    assert "mornye_s3_distributed_array" in event_types(result)
    assert "starfield_r5_same_action" not in event_types(result)
    distributed = next(event for event in result.account_constellation_events if event["event_type"] == "mornye_s3_distributed_array")
    assert distributed["concerto_gain"] == 25.0
    assert mornye.state.concerto_energy["mornye"] == 51.0
    assert mornye.state.character_mechanics_state["_account_constellation"]["mornye_s3_icd_remaining"] > 0.0
    assert mornye.state.character_mechanics_state["_account_constellation"]["starfield_icd_remaining"] == 0.0
    print("account_constellation_v121_real_resource_state_smoke_test ok")


if __name__ == "__main__":
    main()
