from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.buff_system import apply_buff
from simulator.simulation import Simulation
from lynae_spray_paint_test_helpers import TUNE_RUPTURE_REF


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-8) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance), (
        f"{label}: expected {expected}, got {actual}"
    )


def active_buff(sim: Simulation, buff_id: str):
    return next(buff for buff in sim.state.active_buffs if buff.buff_id == buff_id)


def active_buff_remaining(sim: Simulation, buff_id: str) -> float:
    return float(active_buff(sim, buff_id).remaining_duration)


def active_buff_remaining_map(sim: Simulation, buff_ids: list[str]) -> dict[str, float]:
    return {buff_id: active_buff_remaining(sim, buff_id) for buff_id in buff_ids}


def setup_interfered_marker(sim: Simulation) -> None:
    sim.state.active_character_id = "mornye"
    mornye_state = sim.state.character_mechanics_state["mornye"]
    mornye_state["mode"] = "wide_field_observation"
    mornye_state["relative_momentum"] = 100.0
    assert sim.execute_action("mornye_heavy_attack")

    sim.state.enemy_tune_break_available = True
    sim.state.enemy_mistune_active = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_tune_shift_remaining = 8.0
    assert sim.execute_action("mornye_tune_break")
    row = sim.timeline[-1]
    assert row.mornye_interfered_marker_applied is True
    assert_close(row.interfered_marker_damage_taken_amp, 0.3856, "Interfered Marker amp")
    assert_close(sim.state.interfered_marker_remaining, 8.0, "Interfered Marker state duration")
    assert_close(active_buff_remaining(sim, "mornye_interfered_marker_damage_amp"), 8.0, "Interfered Marker buff")


def execute_zero_combat_liberation(sim: Simulation):
    sim.state.active_character_id = "aemeath"
    sim.state.resonance_energy["aemeath"] = sim.characters["aemeath"].resonance_energy_max
    current_before = sim.state.current_time
    combat_before = sim.state.combat_time
    assert sim.execute_action("aemeath_resonance_liberation")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "aemeath_liberation_overdrive"
    assert row.action_time > 0.0
    assert_close(row.effective_combat_time_cost, 0.0, "Aemeath Overdrive combat time")
    assert_close(sim.state.current_time, current_before + row.action_time, "current_time advances by action_time")
    assert_close(sim.state.combat_time, combat_before, "combat_time does not advance during global stop")
    return row


def apply_duration_probe_buff(sim: Simulation, remaining_duration: float = 20.0) -> None:
    buff = sim.buffs["dummy_support_damage_amp"].model_copy(deep=True)
    apply_buff(sim.state, buff, "dummy_support")
    active_buff(sim, buff.id).remaining_duration = remaining_duration


def setup_partial_seraphic(sim: Simulation) -> None:
    state = sim.state.character_mechanics_state["aemeath"]
    state["form"] = "aemeath"
    state["seraphic_duo_remaining"] = 5.0
    state["synchronization_rate"] = 100.0


def test_zero_combat_time_action() -> None:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="mornye")
    setup_interfered_marker(sim)
    apply_duration_probe_buff(sim)
    unrelated_before = active_buff_remaining(sim, "dummy_support_damage_amp")

    execute_zero_combat_liberation(sim)

    assert_close(sim.state.interfered_marker_remaining, 8.0, "Interfered Marker after zero combat action")
    assert_close(
        active_buff_remaining(sim, "mornye_interfered_marker_damage_amp"),
        8.0,
        "Interfered Marker buff after zero combat action",
    )
    assert_close(sim.state.interfered_marker_damage_taken_amp, 0.3856, "Interfered Marker amp still active")
    assert_close(active_buff_remaining(sim, "dummy_support_damage_amp"), unrelated_before, "unrelated buff remains")


def test_partial_combat_time_action() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    setup_partial_seraphic(sim)
    apply_duration_probe_buff(sim)
    before = active_buff_remaining(sim, "dummy_support_damage_amp")

    assert sim.execute_action("aemeath_resonance_skill")
    row = sim.timeline[-1]
    assert row.resolved_action_id == "aemeath_seraphic_duet_overturn"
    assert row.action_time > row.effective_combat_time_cost > 0.0
    expected = before - row.effective_combat_time_cost
    old_wrong = before - row.action_time
    after = active_buff_remaining(sim, "dummy_support_damage_amp")
    assert_close(after, expected, "partial time-stop buff duration")
    assert not math.isclose(after, old_wrong, rel_tol=0.0, abs_tol=1e-8), "buff ticked by action_time"


def test_ordinary_action_single_tick() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    apply_duration_probe_buff(sim, remaining_duration=8.0)
    before = active_buff_remaining(sim, "dummy_support_damage_amp")

    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    assert_close(row.action_time, row.effective_combat_time_cost, "ordinary action time parity")
    assert_close(
        active_buff_remaining(sim, "dummy_support_damage_amp"),
        before - row.effective_combat_time_cost,
        "ordinary buff duration decremented once",
    )


def test_simultaneous_effects_and_persistent_windows() -> None:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="mornye")
    setup_interfered_marker(sim)

    apply_buff(sim.state, sim.buffs["lynae_liberation_party_damage_amp"], "lynae")
    for buff_id in (
        "lynae_outro_all_damage_amp",
        "lynae_outro_liberation_damage_amp",
        "static_mist_incoming_atk",
        "pact_neonlight_incoming_atk",
        "hyvatia_incoming_all_attribute_damage_bonus",
    ):
        assert sim._apply_specific_character_buff(
            buff_id=buff_id,
            source_character_id="lynae",
            target_character_id="aemeath",
            application_time=sim.state.current_time,
            metadata={"event_source": "combat_time_duration_test"},
        )
    mornye_state = sim.state.character_mechanics_state["mornye"]
    lynae_state = sim.state.character_mechanics_state["lynae"]
    mornye_state["syntony_field_remaining"] = 25.0
    sim.schedule_effect(
        instance_id="lynae_spray_paint_flux:lynae",
        effect_id="lynae_spray_paint",
        source_character_id="lynae",
        source_action_id="lynae_visual_impact",
        payload_action_id="lynae_spray_paint_flux_application",
        remaining_duration=5.0,
        tick_interval=10.0,
        time_until_next_tick=10.0,
        payload_event_type="status_application",
        scheduled_resource_policy="none",
        source_status="combat_time_duration_test",
        source_ref="combat_time_duration_test",
        metadata={
            "scheduled_status_effect_id": "lynae_photocromic_flux",
            "paint_mode_snapshot": "tune_rupture",
            "target_shift_state_snapshot": "tune_rupture_shifting",
            "source_row": TUNE_RUPTURE_REF,
            "source_ref": TUNE_RUPTURE_REF,
            "target_presence_assumption": "single_target_remains_inside_paint_area",
        },
    )
    lynae_state["spray_paint_window_remaining"] = 5.0

    buff_ids = [
        "mornye_interfered_marker_damage_amp",
        "lynae_liberation_party_damage_amp",
        "lynae_outro_all_damage_amp",
        "lynae_outro_liberation_damage_amp",
        "static_mist_incoming_atk",
        "pact_neonlight_incoming_atk",
        "hyvatia_incoming_all_attribute_damage_bonus",
    ]
    before_zero = active_buff_remaining_map(sim, buff_ids)
    state_before_zero = {
        "interfered_marker": sim.state.interfered_marker_remaining,
        "syntony_field": mornye_state["syntony_field_remaining"],
        "spray_paint": lynae_state["spray_paint_window_remaining"],
    }

    execute_zero_combat_liberation(sim)
    assert active_buff_remaining_map(sim, buff_ids) == before_zero
    assert_close(sim.state.interfered_marker_remaining, state_before_zero["interfered_marker"], "state marker zero")
    assert_close(mornye_state["syntony_field_remaining"], state_before_zero["syntony_field"], "Syntony zero")
    assert_close(lynae_state["spray_paint_window_remaining"], state_before_zero["spray_paint"], "Spray Paint zero")

    before_ordinary = active_buff_remaining_map(sim, buff_ids)
    state_before_ordinary = {
        "interfered_marker": sim.state.interfered_marker_remaining,
        "syntony_field": mornye_state["syntony_field_remaining"],
        "spray_paint": lynae_state["spray_paint_window_remaining"],
    }
    assert sim.execute_action("aemeath_basic_attack")
    row = sim.timeline[-1]
    elapsed = row.effective_combat_time_cost
    assert elapsed > 0.0
    for buff_id, before in before_ordinary.items():
        assert_close(active_buff_remaining(sim, buff_id), before - elapsed, f"{buff_id} ordinary tick")
        assert active_buff(sim, buff_id).target_character_id in {None, "aemeath"}
    assert_close(sim.state.interfered_marker_remaining, state_before_ordinary["interfered_marker"] - elapsed, "marker ordinary")
    assert_close(mornye_state["syntony_field_remaining"], state_before_ordinary["syntony_field"] - elapsed, "Syntony ordinary")
    assert_close(lynae_state["spray_paint_window_remaining"], state_before_ordinary["spray_paint"] - elapsed, "Spray Paint ordinary")


def test_expiration_after_action_start_application() -> None:
    baseline = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    assert baseline.execute_action("aemeath_basic_attack")
    first_baseline_damage = baseline.timeline[-1].damage
    assert baseline.execute_action("aemeath_basic_attack")
    second_baseline_damage = baseline.timeline[-1].damage

    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    apply_duration_probe_buff(sim, remaining_duration=0.1)
    assert sim.execute_action("aemeath_basic_attack")
    first = sim.timeline[-1]
    assert first.damage > first_baseline_damage
    assert not any(buff.buff_id == "dummy_support_damage_amp" for buff in sim.state.active_buffs)

    assert sim.execute_action("aemeath_basic_attack")
    second = sim.timeline[-1]
    assert_close(second.damage, second_baseline_damage, "expired buff absent from following action", tolerance=1e-6)


def main() -> None:
    test_zero_combat_time_action()
    test_partial_combat_time_action()
    test_ordinary_action_single_tick()
    test_simultaneous_effects_and_persistent_windows()
    test_expiration_after_action_start_application()
    print("combat_time_effect_duration_smoke_test ok")


if __name__ == "__main__":
    main()
