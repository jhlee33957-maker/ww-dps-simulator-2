from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.buff_system import apply_buff, support_stat_context
from simulator.simulation import Simulation


def main() -> None:
    buffs = {row["id"]: row for row in json.loads((ROOT / "data/buffs.json").read_text(encoding="utf-8"))}
    buff = buffs["lynae_visual_impact_tune_break_boost"]
    assert buff["support_stat_modifiers"]["tune_break_boost_points_add"] == 40.0
    assert buff["metadata"]["implementation_status"] == "implemented_single_target_formula_hook"

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    before = support_stat_context(sim.characters["lynae"], sim.state, sim.buffs)
    assert before["base_tune_break_boost_points"] == 0.0
    assert before["runtime_tune_break_boost_points_bonus"] == 0.0
    assert before["current_tune_break_boost_points"] == 0.0

    apply_buff(sim.state, sim.buffs["lynae_visual_impact_tune_break_boost"], "lynae")
    after = support_stat_context(sim.characters["lynae"], sim.state, sim.buffs)
    assert after["base_tune_break_boost_points"] == 0.0
    assert after["runtime_tune_break_boost_points_bonus"] == 40.0
    assert after["current_tune_break_boost_points"] == 40.0
    print("lynae_visual_impact_tune_break_boost_formula_hook_smoke_test ok")


if __name__ == "__main__":
    main()
