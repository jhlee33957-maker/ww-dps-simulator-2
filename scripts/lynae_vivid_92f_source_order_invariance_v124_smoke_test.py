from account_constellation_v121_runtime_test_utils import make_account_sim
from stage2c_timing_test_support import ARRAY_ID, HEAVY_ID
from v124_timing_test_support import make_sim


VIVID = "lynae_to_a_vivid_tomorrow"


def vivid_packet_order(sim) -> list[tuple[int, str, int]]:
    source = next(instance for instance in sim.state.ongoing_action_instances if instance.source_action_id == VIVID)
    sim.advance_timing_runtime(max(0.0, source.action_end_wall_time - sim.state.current_time))
    return [
        (
            round((event["scheduled_wall_time"] - source.start_wall_time) * 60),
            event["packet_group_id"],
            event["packet_occurrence_index"],
        )
        for event in sim.state.scheduled_packet_event_log
        if event.get("source_action_id") == VIVID and event.get("packet_instance_id")
    ]


def fresh_case() -> list[tuple[int, str, int]]:
    sim = make_sim("lynae")
    assert sim.execute_action(VIVID)
    return vivid_packet_order(sim)


def account_prefix_case() -> list[tuple[int, str, int]]:
    sim = make_account_sim("mornye")
    prefix = [
        "mornye_basic_stage_1", "mornye_basic_stage_2", "swap_to_aemeath",
        "aemeath_heavy_aemeath_charged_2", "swap_to_mornye", "mornye_basic_stage_1",
        "mornye_heavy_geopotential_shift", "swap_to_lynae",
        "lynae_resonance_liberation_prismatic_overblast", VIVID,
        "swap_to_mornye", ARRAY_ID, HEAVY_ID,
    ]
    assert all(sim.execute_action(action_id) for action_id in prefix)
    return vivid_packet_order(sim)


def main() -> None:
    fresh = fresh_case()
    account_prefix = account_prefix_case()
    expected_92f = [
        (92, "row_2697_packet_family", 9),
        (92, "row_2698_packet_family", 1),
    ]
    assert [item for item in fresh if item[0] == 92] == expected_92f
    assert [item for item in account_prefix if item[0] == 92] == expected_92f
    assert fresh == account_prefix
    print("lynae_vivid_92f_source_order_invariance_v124_smoke_test ok 92F=2697#9,2698#1")


if __name__ == "__main__":
    main()
