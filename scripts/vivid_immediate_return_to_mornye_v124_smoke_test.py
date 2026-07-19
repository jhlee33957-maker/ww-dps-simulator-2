from __future__ import annotations

from v124_timing_test_support import VIVID_ID, execute_immediate_return_route


def main() -> None:
    sim = execute_immediate_return_route()
    assert sim.state.active_character_id == "mornye"
    assert sim.state.current_time == 239 / 60
    assert sim.state.combat_time == 1 / 60
    assert all(row.selected_action_id != "short_wait" for row in sim.timeline)
    vivid = next(item for item in sim.state.ongoing_action_instances if item.source_action_id == VIVID_ID)
    assert not vivid.ended and vivid.owner_character_persistent and vivid.owner_character_executing
    assert "lynae" in sim.state.persistent_off_field_character_ids
    print("vivid_immediate_return_to_mornye_v124_smoke_test ok")


if __name__ == "__main__":
    main()
