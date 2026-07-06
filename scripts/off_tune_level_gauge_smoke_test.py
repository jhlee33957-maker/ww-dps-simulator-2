from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-6) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_test_party")
    assert_close(sim.state.enemy_off_tune_max, 3920.0, "enemy_off_tune_max")
    assert sim.actions["mornye_basic_stage_1"].off_tune_value == 28.0
    assert sim.actions["aemeath_basic_form_stage_1"].off_tune_value == 26.64

    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_basic_stage_1"
    assert_close(row.off_tune_added, 28.0, "base Off-Tune added")
    assert_close(sim.state.enemy_off_tune_current, 28.0, "current Off-Tune")
    assert sim.state.tune_break_damage_total == 0.0

    sim.state.character_mechanics_state["mornye"]["syntony_field_remaining"] = 25.0
    sim.state.character_mechanics_state["mornye"]["high_syntony_field_remaining"] = 25.0
    from simulator.echo_sets import apply_syntony_field_off_tune_buff

    apply_syntony_field_off_tune_buff(state=sim.state, constellation=0)
    before = sim.state.enemy_off_tune_current
    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    assert_close(row.current_off_tune_buildup_rate, 1.5, "Syntony/High Syntony rate")
    assert_close(row.off_tune_added, 33.0 * 1.5, "Syntony Off-Tune added")
    assert_close(sim.state.enemy_off_tune_current, before + 49.5, "Syntony current")

    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max - sim.actions["mornye_basic_stage_3"].off_tune_value
    assert sim.execute_action("mornye_basic_attack")
    assert sim.state.enemy_mistune_active is True
    assert sim.state.enemy_tune_break_available is True
    assert sim.state.tune_break_damage_total == 0.0

    sim.state.enemy_tune_break_cooldown_remaining = 8.0
    sim.state.enemy_mistune_active = False
    sim.state.enemy_tune_break_available = False
    sim.state.enemy_off_tune_current = sim.state.enemy_off_tune_max - 1.0
    assert sim.execute_action("mornye_basic_attack")
    assert sim.state.enemy_tune_break_available is False
    assert sim.state.off_tune_accumulation_logs[-1]["behavior"] == "cooldown_blocks_mistune_reentry"

    print("off_tune_level_gauge_smoke_test ok")


if __name__ == "__main__":
    main()
