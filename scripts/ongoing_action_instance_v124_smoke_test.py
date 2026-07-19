from __future__ import annotations

from v124_timing_test_support import LIBERATION_ID, make_sim
from simulator.action_timing_contract import start_ongoing_action
from simulator.models import OngoingActionInstance


def main() -> None:
    sim = make_sim("lynae")
    instance = start_ongoing_action(sim.state, sim.actions[LIBERATION_ID], sim.action_timing_contracts[LIBERATION_ID])
    restored = OngoingActionInstance.model_validate(instance.model_dump(mode="json"))
    assert restored.action_instance_id == instance.action_instance_id
    assert restored.owner_character_id == "lynae"
    assert restored.start_wall_time == restored.start_combat_time == 0.0
    assert restored.same_character_lock_until_wall_time == 238 / 60
    assert restored.swap_lock_until_wall_time == 240 / 60
    assert restored.action_end_wall_time == 299 / 60
    assert restored.scheduled_packet_instances == []
    print("ongoing_action_instance_v124_smoke_test ok")


if __name__ == "__main__":
    main()
