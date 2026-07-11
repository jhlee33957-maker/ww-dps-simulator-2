from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
DISCORD_COOLDOWN_KEY = "mornye:discord:resonance_skill_concerto_restore"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol), f"{label}: expected {expected}, got {actual}"


def main() -> None:
    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID, initial_active_character="mornye")
    assert sim.characters["mornye"].weapon["weapon_id"] == "discord"
    assert sim.characters["mornye"].weapon["rank"] == 5
    assert sim.state.active_character_id == "mornye"
    assert sim.state.concerto_energy["mornye"] == 0.0

    assert sim.execute_action("mornye_resonance_skill")
    first_skill = sim.timeline[-1]
    assert first_skill.resolved_action_id == "mornye_skill_expectation_error"
    assert first_skill.weapon_id == "discord"
    assert first_skill.weapon_rank == 5
    assert first_skill.weapon_effect_triggered is True
    assert_close(first_skill.concerto_energy_restored_by_weapon, 16.0, "first Discord restore")
    assert_close(first_skill.weapon_effect_cooldown_seconds, 20.0, "Discord ICD")
    assert_close(sim.state.weapon_effect_cooldowns[DISCORD_COOLDOWN_KEY], 20.0, "Discord ICD starts")

    rest_mass_after_basics: list[float] = []
    expected_stage_gains = [20.0, 43.0, 37.0]
    previous_rest_mass = sim.state.character_mechanics_state["mornye"]["rest_mass_energy"]
    for index, expected_gain in enumerate(expected_stage_gains, start=1):
        assert sim.execute_action("mornye_basic_attack")
        row = sim.timeline[-1]
        assert row.resolved_action_id == f"mornye_basic_stage_{index}"
        rest_mass = sim.state.character_mechanics_state["mornye"]["rest_mass_energy"]
        assert_close(rest_mass - previous_rest_mass, expected_gain, f"basic stage {index} rest-mass gain")
        rest_mass_after_basics.append(rest_mass)
        previous_rest_mass = rest_mass
    assert rest_mass_after_basics == [20.0, 63.0, 100.0]

    assert sim.execute_action("mornye_heavy_attack")
    first_heavy = sim.timeline[-1]
    assert first_heavy.resolved_action_id == "mornye_heavy_geopotential_shift"
    assert sim.state.character_mechanics_state["mornye"]["mode"] == "wide_field_observation"

    assert sim.execute_action("mornye_resonance_liberation")
    assert sim.timeline[-1].resolved_action_id == "mornye_liberation_critical_protocol"

    assert sim.execute_action("mornye_resonance_skill")
    second_skill = sim.timeline[-1]
    assert second_skill.resolved_action_id == "mornye_skill_distributed_array"
    assert second_skill.weapon_id == "discord"
    assert second_skill.weapon_effect_cooldown_blocked is True
    assert_close(second_skill.concerto_energy_restored_by_weapon, 0.0, "blocked Discord restore")

    for expected_resolved_id in (
        "mornye_wfo_basic_stage_1",
        "mornye_wfo_basic_stage_2",
        "mornye_wfo_basic_stage_3",
    ):
        assert sim.execute_action("mornye_basic_attack")
        assert sim.timeline[-1].resolved_action_id == expected_resolved_id

    assert sim.execute_action("mornye_heavy_attack")
    final_heavy = sim.timeline[-1]
    assert final_heavy.resolved_action_id == "mornye_heavy_inversion"

    assert sim.state.weapon_effect_trigger_counts.get(DISCORD_COOLDOWN_KEY) == 1
    assert sim.state.weapon_effect_cooldown_blocked_counts.get(DISCORD_COOLDOWN_KEY) == 1
    assert_close(sim.state.concerto_energy["mornye"], 100.0, "clamped Mornye Concerto")
    assert_close(sim.state.wasted_concerto_energy["mornye"], 1.44, "wasted Mornye Concerto")
    assert_close(
        sim.state.concerto_energy["mornye"] + sim.state.wasted_concerto_energy["mornye"],
        101.44,
        "pre-clamp Mornye Concerto",
    )

    assert sim.execute_action("swap_to_lynae")
    swap = sim.timeline[-1]
    assert swap.action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert swap.resolved_action_id == "transition:lynae_intro_time_to_show_some_colors"
    assert swap.incoming_character_id == "lynae"
    assert swap.incoming_intro_event_id == "lynae_intro_time_to_show_some_colors"
    assert swap.outgoing_outro_applied is True
    assert swap.swap_timing_is_placeholder is False
    assert sim.state.active_character_id == "lynae"
    assert_close(sim.state.concerto_energy["mornye"], 0.0, "Mornye Concerto consumed")

    print("mornye_discord_r5_no_counter_opener_smoke_test ok")


if __name__ == "__main__":
    main()
