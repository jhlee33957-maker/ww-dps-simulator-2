from __future__ import annotations

from v124_timing_test_support import VIVID_ID, make_sim
from simulator.action_timing_contract import handle_character_swap, start_ongoing_action


def main() -> None:
    sim = make_sim("lynae")
    instance = start_ongoing_action(sim.state, sim.actions[VIVID_ID], sim.action_timing_contracts[VIVID_ID])
    sim.advance_timing_runtime(1 / 60)
    sim.state.active_character_id = "mornye"
    handle_character_swap(sim.state, "lynae")
    assert instance.owner_character_persistent
    assert instance.owner_character_executing
    assert "lynae" in sim.state.persistent_off_field_character_ids
    assert all(not packet.cancelled for packet in sim.state.scheduled_packet_instances)
    print("lynae_vivid_early_swap_persistence_v124_smoke_test ok")


if __name__ == "__main__":
    main()

