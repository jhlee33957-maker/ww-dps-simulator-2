from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.action_start_effect_snapshot_smoke_test import EVERBRIGHT_BUFF_ID, everbright_sim
from scripts.combat_time_effect_duration_smoke_test import PARTY_ID, active_buff
from simulator.simulation import Simulation
from simulator.weapon_effects import weapon_effect_uptime_seconds


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def execute_zero_combat_liberation(sim: Simulation):
    sim.state.active_character_id = "aemeath"
    sim.state.resonance_energy["aemeath"] = sim.characters["aemeath"].resonance_energy_max
    current_before = sim.state.current_time
    combat_before = sim.state.combat_time
    assert sim.execute_action("aemeath_resonance_liberation")
    row = sim.timeline[-1]
    assert row.action_time > 0.0
    assert_close(row.effective_combat_time_cost, 0.0, "zero combat time")
    assert_close(sim.state.current_time, current_before + row.action_time, "current_time action elapsed")
    assert_close(sim.state.combat_time, combat_before, "combat_time frozen")
    return row


def test_zero_combat_time_uptime_freezes() -> None:
    sim = everbright_sim()
    before_remaining = active_buff(sim, EVERBRIGHT_BUFF_ID).remaining_duration
    before_current = sim.state.current_time
    before_combat = sim.state.combat_time
    before_uptime = weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time)

    execute_zero_combat_liberation(sim)

    assert sim.state.current_time > before_current
    assert_close(sim.state.combat_time, before_combat, "combat time after zero")
    assert_close(active_buff(sim, EVERBRIGHT_BUFF_ID).remaining_duration, before_remaining, "remaining after zero")
    assert_close(
        weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time),
        before_uptime,
        "uptime after zero",
    )


def test_ordinary_uptime_uses_combat_time() -> None:
    sim = everbright_sim()
    before_remaining = active_buff(sim, EVERBRIGHT_BUFF_ID).remaining_duration
    before_uptime = weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time)

    assert sim.execute_action("aemeath_basic_form_stage_1")
    row = sim.timeline[-1]
    assert row.effective_combat_time_cost > 0.0
    after_uptime = weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time)
    assert_close(
        active_buff(sim, EVERBRIGHT_BUFF_ID).remaining_duration,
        before_remaining - row.effective_combat_time_cost,
        "ordinary remaining",
    )
    assert_close(after_uptime - before_uptime, row.effective_combat_time_cost, "ordinary uptime delta")


def test_partial_expiration_uptime_caps_at_remaining_duration() -> None:
    sim = everbright_sim()
    before_uptime = weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time)
    active_buff(sim, EVERBRIGHT_BUFF_ID).remaining_duration = 0.1

    assert sim.execute_action("aemeath_heavy_aemeath_charged_1")
    row = sim.timeline[-1]
    assert row.effective_combat_time_cost > 0.1
    assert row.everbright_polestar_liberation_penetration_active is True
    assert not any(buff.buff_id == EVERBRIGHT_BUFF_ID for buff in sim.state.active_buffs)
    after_uptime = weapon_effect_uptime_seconds(sim.state, EVERBRIGHT_BUFF_ID, sim.state.combat_time)
    assert_close(after_uptime - before_uptime, 0.1, "partial expiration uptime")

    assert sim.execute_action("aemeath_basic_form_stage_1")
    assert sim.timeline[-1].everbright_polestar_liberation_penetration_active is False


def test_zero_combat_time_generic_buff_uptime_freezes() -> None:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="aemeath")
    # A real party profile is loaded here to exercise summary/reporting clocks alongside action timing.
    assert sim.characters["aemeath"].id == "aemeath"
    execute_zero_combat_liberation(sim)
    summary = sim.summary()
    assert_close(summary.final_time, 0.0, "summary combat time frozen")
    assert summary.final_action_time > 0.0


def main() -> None:
    test_zero_combat_time_uptime_freezes()
    test_ordinary_uptime_uses_combat_time()
    test_partial_expiration_uptime_caps_at_remaining_duration()
    test_zero_combat_time_generic_buff_uptime_freezes()
    print("combat_time_uptime_reporting_smoke_test ok")


if __name__ == "__main__":
    main()
