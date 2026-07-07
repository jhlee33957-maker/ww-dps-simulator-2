from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    weapons = json.loads((ROOT / "data/weapons.json").read_text(encoding="utf-8"))
    static_mist = weapons["weapons"]["static_mist"]
    assert static_mist["rank_values"]["1"]["energy_regen_static_bonus"] == 0.128
    assert static_mist["static_stats_already_in_profile_supported"] is True

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.state.action_log[-1]
    assert row["outgoing_character_id"] == "lynae"
    assert row["incoming_character_id"] == "aemeath"
    assert row["lynae_static_mist_incoming_atk_buff"] is True
    assert row["lynae_static_mist_incoming_atk_value"] == 0.10
    active = next(buff for buff in sim.state.active_buffs if buff.buff_id == "static_mist_incoming_atk")
    assert abs(active.remaining_duration - 14.0) < 1e-9
    assert active.stack_count == 1
    assert active.target_character_id == "aemeath"
    print("static_mist_weapon_smoke_test ok")


if __name__ == "__main__":
    main()
