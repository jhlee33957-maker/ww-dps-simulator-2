from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.echo_sets import apply_syntony_field_off_tune_buff
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def make_sim() -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        initial_active_character="mornye",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
        transition_config={"mechanics": {"mornye": {"mornye_heal_event_mode": "simplified_syntony_field_uptime"}}},
    )
    sim.characters["mornye"].weapon = {
        "weapon_id": "starfield_calibrator",
        "weapon_type": "broadblade",
        "rank": 1,
        "static_stats_already_in_profile": True,
    }
    sim.state.resonance_energy["mornye"] = sim.characters["mornye"].resonance_energy_max
    sim.state.character_states["mornye"]["syntony_field_remaining"] = 25.0
    apply_syntony_field_off_tune_buff(state=sim.state, constellation=0)
    return sim


def test_high_syntony_weapon_source_status_collision_guard() -> None:
    sim = make_sim()
    assert sim.execute_action("mornye_resonance_liberation")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "mornye_liberation_critical_protocol"
    assert row.high_syntony_field_same_action_application is True
    assert row.team_heal_event_triggered is True
    assert row.weapon_effect_triggered is True
    assert row.weapon_effect_id == "heal_party_crit_damage_buff"
    assert row.weapon_effect_source_status == "user_supplied_weapon_tooltip"
    assert row.source_status is None or isinstance(row.source_status, str)
    assert row.mechanic_event_source_status is None or isinstance(row.mechanic_event_source_status, str)
    assert row.weapon_effect_logs
    for log in row.weapon_effect_logs:
        assert log["weapon_effect_source_status"] == "user_supplied_weapon_tooltip"
        assert "source_status" not in log
    assert all("source_status" not in log for log in sim.state.weapon_effect_logs)


def main() -> None:
    test_high_syntony_weapon_source_status_collision_guard()
    print("weapon_effect_source_status_collision_guard_smoke_test ok")


if __name__ == "__main__":
    main()
