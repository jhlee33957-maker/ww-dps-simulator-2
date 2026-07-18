from __future__ import annotations

from account_constellation_v121_runtime_test_utils import event_types, make_account_sim, ready_mornye_distributed_array


def main() -> None:
    sim = make_account_sim("mornye")
    ready_mornye_distributed_array(sim)
    assert sim.execute_action("mornye_skill_distributed_array")
    result = sim.last_action_result
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert "mornye_s3_distributed_array" in event_types(result)
    assert "starfield_r5_same_action" not in event_types(result)
    assert account["starfield_icd_remaining"] == 0.0
    distributed = next(event for event in result.account_constellation_events if event["event_type"] == "mornye_s3_distributed_array")
    assert distributed["concerto_gain"] == 25.0
    assert sim.state.concerto_energy["mornye"] == 51.0
    print("mornye_s3_starfield_no_duplicate_v121_smoke_test ok")


if __name__ == "__main__":
    main()
