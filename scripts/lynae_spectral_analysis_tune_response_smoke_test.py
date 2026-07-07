from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def main() -> None:
    responses = {row["id"]: row for row in json.loads((ROOT / "data/tune_responses.json").read_text(encoding="utf-8"))}
    response = responses["lynae_spectral_analysis"]
    assert response["formula_type"] == "tune_response"
    assert response["multiplier"] == 18.8075
    assert response["source_status"] == "workbook_confirmed"
    assert response["cooldown_seconds"] == 8.0
    assert response["policy_selectable"] is False
    assert response["c2_enabled_by_default"] is False

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert "lynae_tune_response_spectral_analysis" not in sim.get_policy_action_ids()
    sim.state.active_character_id = "aemeath"
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 30.0
    assert sim.execute_action("aemeath_tune_break")
    row = sim.state.action_log[-1]
    assert row["lynae_spectral_analysis_triggered"] is True
    assert row["lynae_spectral_analysis_multiplier_used"] == 18.8075
    assert row["lynae_spectral_analysis_c2_disabled_by_default"] is True
    assert row["lynae_spectral_analysis_response_damage"] > 0.0
    print("lynae_spectral_analysis_tune_response_smoke_test ok")


if __name__ == "__main__":
    main()
