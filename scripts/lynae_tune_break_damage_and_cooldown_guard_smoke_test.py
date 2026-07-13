from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


ACTION_ID = "lynae_tune_break"


def main() -> None:
    actions = {action["id"]: action for action in json.loads((ROOT / "data" / "actions.json").read_text(encoding="utf-8"))}
    action = actions[ACTION_ID]
    assert action["action_type"] == "tune_break"
    assert action["action_time"] == 1.6
    assert action["combat_time_cost"] == 0.0
    assert action["damage_multiplier"] == 0.0
    assert action["damage_category"] == "tune_break"
    assert {2488, 2702, 2703, 2704}.issubset(set(action["source_rows"]))
    assert action["source_status"] == "workbook_confirmed_global_timestop_tune_break_damage"
    assert action["data_status"] == "excel_tune_break_single_target_v1"

    assert len(action["hits"]) == 1
    hit = action["hits"][0]
    assert hit["name"] == "Lynae Tune Break tune break"
    assert hit["time"] == 1.6
    assert hit["damage_category"] == "tune_break"
    assert hit["damage_multiplier"] == 0.0
    assert hit["tune_break_multiplier"] == 16.0
    assert "tune_break" in hit["tags"]

    sim = Simulation.from_json(
        ROOT / "data",
        party="aemeath_lynae_enabled_test_party",
        initial_active_character="lynae",
    )
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    assert ACTION_ID in sim.valid_action_ids()

    assert sim.execute_action(ACTION_ID)
    row = sim.timeline[-1]
    assert row.tune_break_damage > 0.0
    assert row.enemy_tune_break_available is False
    assert row.enemy_mistune_active is False
    assert row.enemy_off_tune_current_after_tune_break == 0.0
    assert row.enemy_tune_break_cooldown_started is True
    assert row.enemy_tune_break_cooldown_seconds == 3.0
    assert row.enemy_tune_break_cooldown_remaining == 3.0
    assert sim.state.enemy_tune_break_cooldown_remaining == 3.0
    assert sim.state.enemy_tune_break_available is False
    assert sim.state.enemy_mistune_active is False
    assert sim.state.enemy_off_tune_current == 0.0
    assert ACTION_ID not in sim.valid_action_ids()
    assert sim.execute_action(ACTION_ID) is False

    print("lynae_tune_break_damage_and_cooldown_guard_smoke_test ok")


if __name__ == "__main__":
    main()
