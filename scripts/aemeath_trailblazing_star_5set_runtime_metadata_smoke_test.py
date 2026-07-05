from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.echo_sets import AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
from simulator.simulation import Simulation
from simulator.transition_config import load_transition_config


def config_for_mode(mode: str) -> dict:
    config = copy.deepcopy(load_transition_config(DATA_DIR))
    config.setdefault("mechanics", {}).setdefault("aemeath", {})["aemeath_resonance_mode"] = mode
    return config


def test_profile_and_buff_metadata() -> None:
    profiles = json.loads((DATA_DIR / "build_profiles.json").read_text(encoding="utf-8-sig"))
    profile = profiles["profiles"]["aemeath"]["aemeath_user_real_01"]
    trail = profile["echo_sets"]["trailblazing_star"]
    assert trail["pieces"] == 5
    assert trail["static_2set_already_in_profile"] is True
    assert trail["conditional_5set_enabled"] is True
    assert trail["conditional_5set_status"] == "implemented"
    assert trail["source_status"] == "user_supplied_set_tooltip"
    assert trail["trigger_event_tags"] == ["fusion_burst", "tune_rupture_shifting"]
    assert trail["buff_id"] == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
    assert profile["damage_bonuses"]["by_element"]["generic"] == 0.4
    assert profile["damage_bonuses"]["by_element"]["fusion"] == 0.4

    buffs = {
        row["id"]: row
        for row in json.loads((DATA_DIR / "buffs.json").read_text(encoding="utf-8-sig"))
    }
    buff = buffs[AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert buff["duration"] == 8.0
    assert buff["max_stacks"] == 1
    assert buff["stacking_rule"] == "refresh_duration"
    assert buff["target_scope"] == "self"
    assert buff["target_character_id"] == "aemeath"
    assert buff["source_character_id"] == "aemeath"
    assert buff["stat_modifiers"]["crit_rate"] == 0.2
    assert buff["damage_bonus_by_element"]["fusion"] == 0.2
    assert buff["metadata"]["source_type"] == "echo_set"


def test_effective_summary_and_runtime_diagnostics() -> None:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath",
        transition_config=config_for_mode("fusion_burst"),
        build_profile_overrides={"aemeath": "aemeath_user_real_01"},
    )
    assert sim.characters["aemeath"].echo_sets["trailblazing_star"]["pieces"] == 5
    assert sim.effective_build_stats_summary["aemeath"]["echo_sets"]["trailblazing_star"]["pieces"] == 5

    summary = sim.summary()
    assert summary.active_echo_sets["aemeath"]["trailblazing_star"]["conditional_5set_enabled"] is True
    assert summary.aemeath_trailblazing_star_5set_enabled is True
    assert summary.aemeath_trailblazing_star_5set_trigger_event_tags == ["fusion_burst", "tune_rupture_shifting"]
    assert summary.aemeath_trailblazing_star_5set_trigger_count == 0
    assert summary.echo_set_active_buffs == []

    assert sim.execute_action("aemeath_basic_form_stage_3")
    triggered_summary = sim.summary()
    row = triggered_summary.timeline[-1]
    assert row.echo_set_triggered_buff_ids == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert row.aemeath_trailblazing_star_5set_active is True
    assert triggered_summary.echo_set_active_buffs == [AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID]
    assert triggered_summary.aemeath_trailblazing_star_5set_buff_windows


def test_source_note_files_exist() -> None:
    markdown_path = PROJECT_ROOT / "reports" / "aemeath_trailblazing_star_5set_runtime_buff_note.md"
    json_path = DATA_DIR / "extracted" / "aemeath_trailblazing_star_5set_runtime_buff_note.json"
    assert markdown_path.exists()
    assert json_path.exists()
    note = json.loads(json_path.read_text(encoding="utf-8-sig"))
    assert note["implemented_buff_id"] == AEMEATH_TRAILBLAZING_STAR_5SET_BUFF_ID
    assert note["static_2set_already_in_profile"] is True
    assert "fusion_burst_explosion_damage" in note["unsupported_mechanics"]


def main() -> None:
    test_profile_and_buff_metadata()
    test_effective_summary_and_runtime_diagnostics()
    test_source_note_files_exist()
    print("aemeath_trailblazing_star_5set_runtime_metadata_smoke_test ok")


if __name__ == "__main__":
    main()
