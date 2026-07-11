from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
AEMEATH_OPENING = [
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_basic_attack",
    "aemeath_resonance_skill",
]
MORNYE_OPENER = [
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
    "mornye_resonance_liberation",
    "mornye_resonance_skill",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_basic_attack",
    "mornye_heavy_attack",
]
LYNAE_CHECKPOINTS = [
    ("lynae_resonance_skill", "lynae_resonance_skill_palette", 2117.10, 130.83),
    ("lynae_spark_collision", "lynae_spark_collision_lv3", 2511.60, 394.50),
    ("lynae_polychrome_leap", "lynae_polychrome_leap_stage_1", 2583.60, 72.00),
    ("lynae_polychrome_leap", "lynae_polychrome_leap_stage_2", 2655.60, 72.00),
    ("lynae_polychrome_leap", "lynae_polychrome_leap_stage_3", 2702.10, 46.50),
    ("lynae_visual_impact", "lynae_visual_impact", 3616.50, 914.40),
    ("lynae_resonance_liberation", "lynae_resonance_liberation_prismatic_overblast", 3920.00, 720.00),
]


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-6) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party=PARTY_ID, initial_active_character="aemeath")

    for action_id in AEMEATH_OPENING:
        assert sim.execute_action(action_id), action_id
    assert_close(sim.state.enemy_off_tune_current, 263.25, "after Aemeath opening")

    assert sim.execute_action("swap_to_mornye")
    for action_id in MORNYE_OPENER:
        assert sim.execute_action(action_id), action_id
    assert_close(sim.state.enemy_off_tune_current, 1826.67, "after Mornye opener")

    assert sim.execute_action("swap_to_lynae")
    intro = sim.timeline[-1]
    assert intro.resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert_close(intro.off_tune_value, 106.4, "Lynae Intro base Off-Tune")
    assert_close(intro.off_tune_buildup_rate_used, 1.5, "Lynae Intro Off-Tune rate")
    assert_close(intro.off_tune_added, 159.6, "Lynae Intro Off-Tune added")
    assert_close(sim.state.enemy_off_tune_current, 1986.27, "after Lynae Intro")

    for action_id, resolved_id, expected_off_tune, expected_added in LYNAE_CHECKPOINTS:
        assert sim.execute_action(action_id), action_id
        row = sim.timeline[-1]
        assert row.resolved_action_id == resolved_id
        assert_close(row.off_tune_buildup_rate_used, 1.5, f"{resolved_id} Off-Tune rate")
        assert_close(row.off_tune_added, expected_added, f"{resolved_id} Off-Tune added")
        assert_close(sim.state.enemy_off_tune_current, expected_off_tune, f"after {resolved_id}")

    liberation = sim.timeline[-1]
    assert sim.state.enemy_tune_break_available is True
    assert_close(liberation.enemy_off_tune_current_before, 3616.5, "liberation before Off-Tune")
    assert_close(liberation.enemy_off_tune_current_after, 3920.0, "liberation capped Off-Tune")
    assert_close(sim.state.off_tune_overflow, 416.5, "liberation overflow")

    assert sim.execute_action("lynae_echo_hyvatia")
    hyvatia = sim.timeline[-1]
    assert hyvatia.resolved_action_id == "lynae_echo_hyvatia"
    assert hyvatia.off_tune_value_source_status == "unresolved_echo_off_tune"
    assert_close(hyvatia.off_tune_added, 0.0, "Hyvatia unresolved Off-Tune added")
    assert_close(sim.state.enemy_off_tune_current, 3920.0, "after Hyvatia")

    assert sim.execute_action("swap_to_aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    assert sim.execute_action("aemeath_basic_attack")
    assert sim.state.enemy_tune_break_available is True
    assert_close(sim.state.enemy_off_tune_current, 3920.0, "delayed trigger remains capped")

    assert sim.execute_action("aemeath_tune_break")
    tune_break = sim.timeline[-1]
    assert tune_break.resolved_action_id == "aemeath_tune_break"
    assert_close(tune_break.enemy_off_tune_current_before, 3920.0, "manual Tune Break before")
    assert_close(tune_break.enemy_off_tune_current_after_tune_break, 0.0, "manual Tune Break after")
    assert_close(tune_break.enemy_tune_break_cooldown_remaining, 3.0, "manual Tune Break cooldown")
    assert_close(tune_break.interfered_marker_remaining, 8.0, "manual Tune Break interfered marker")
    assert sim.state.tune_break_action_used_count == 1
    assert sim.state.enemy_tune_break_available is False

    summary = sim.summary()
    assert summary.off_tune_mapping_completeness_status == "incomplete"
    assert summary.unresolved_off_tune_damaging_action_ids == ["lynae_echo_hyvatia"]
    assert "reports/lynae_off_tune_direct_mapping_audit.md" in summary.off_tune_value_mapping_source_report

    print("lynae_off_tune_real_cycle_smoke_test ok")


if __name__ == "__main__":
    main()
