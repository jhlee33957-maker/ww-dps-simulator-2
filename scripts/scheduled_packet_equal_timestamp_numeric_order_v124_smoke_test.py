from v124_timing_test_support import make_sim
from simulator.action_timing_contract import advance_ongoing_action_runtime
from simulator.models import ScheduledPacketInstance


def packet(order: int, scheduled_wall_time: float) -> ScheduledPacketInstance:
    return ScheduledPacketInstance(
        packet_instance_id=f"packet-instance-v124-{order}:synthetic:equal_timestamp:{order}",
        packet_creation_order=order,
        packet_occurrence_index=order,
        action_instance_id="synthetic-action-instance",
        owner_character_id="lynae",
        source_action_id="synthetic_equal_timestamp",
        packet_group_id="synthetic_equal_timestamp",
        scheduled_wall_time=scheduled_wall_time,
        damage_payload={"placeholder": True},
    )


def main() -> None:
    sim = make_sim("lynae")
    sim.state.scheduled_packet_instances.extend(
        [
            packet(9, 1.0),
            packet(10, 1.0),
            packet(11, 1.0),
            packet(99, 2.0),
            packet(100, 2.0),
        ]
    )
    events = advance_ongoing_action_runtime(sim.state, through_wall_time=2.0)
    assert [event["packet_creation_order"] for event in events if event["scheduled_wall_time"] == 1.0] == [9, 10, 11]
    assert [event["packet_creation_order"] for event in events if event["scheduled_wall_time"] == 2.0] == [99, 100]
    assert all("packet_instance_id" in event and "packet_creation_order" in event for event in events)
    print("scheduled_packet_equal_timestamp_numeric_order_v124_smoke_test ok 9<10<11 99<100")


if __name__ == "__main__":
    main()
