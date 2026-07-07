from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def activate_interfered_marker(sim: Simulation) -> None:
    sim.state.target_interfered_state = "tune_rupture_interfered"
    sim.state.target_interfered_remaining = 8.0
    sim.state.interfered_marker_remaining = 8.0
    sim.state.interfered_marker_damage_taken_amp = 0.40


def run_basic(*, marker: bool) -> tuple[float, object]:
    sim = Simulation.from_json(DATA_DIR, party="aemeath")
    if marker:
        activate_interfered_marker(sim)
    assert sim.execute_action("aemeath_basic_form_stage_3")
    row = sim.timeline[-1]
    return row.normal_damage, row


def main() -> None:
    baseline_damage, baseline = run_basic(marker=False)
    amped_damage, amped = run_basic(marker=True)
    assert amped_damage > baseline_damage * 1.399
    assert amped_damage < baseline_damage * 1.401

    direct_hits = [hit for hit in amped.hit_details if hit.get("hit_damage_category") == "normal"]
    assert direct_hits
    assert all(hit["target_damage_taken_amp"] == 0.40 for hit in direct_hits)
    assert all(hit["target_damage_taken_multiplier"] == 1.40 for hit in direct_hits)
    assert all(hit["target_damage_taken_amp_source"] == "mornye_interfered_marker" for hit in direct_hits)
    assert all(hit["target_damage_taken_amp_source_status"] == "workbook_confirmed_row_4164" for hit in direct_hits)
    assert all(hit["interfered_marker_amp_applied_to_direct_damage"] is True for hit in direct_hits)
    assert all(hit["normal_damage_after_target_amp"] > hit["normal_damage_before_target_amp"] for hit in direct_hits)
    assert amped.direct_damage_taken_amp_total_bonus_damage > 0.0
    assert amped.interfered_marker_direct_damage_amp_applied_count == len(direct_hits)
    assert amped.interfered_marker_direct_damage_amp_source_ref == "角色-女!4164"

    base_hit = next(hit for hit in baseline.hit_details if hit.get("hit_damage_category") == "normal")
    amp_hit = direct_hits[0]
    assert amp_hit["element_dmg_bonus"] == base_hit["element_dmg_bonus"]
    assert amp_hit["effective_damage_bonus"] == base_hit["effective_damage_bonus"]
    assert amp_hit["runtime_all_attribute_damage_bonus"] == base_hit["runtime_all_attribute_damage_bonus"]
    assert amp_hit["everbright_polestar_all_attribute_damage_bonus"] == base_hit["everbright_polestar_all_attribute_damage_bonus"]

    print("mornye_interfered_direct_damage_amp_smoke_test ok")


if __name__ == "__main__":
    main()
