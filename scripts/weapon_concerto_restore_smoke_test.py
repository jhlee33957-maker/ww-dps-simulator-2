from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.resource_system import sync_concerto_state
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-8) -> None:
    assert abs(actual - expected) <= tol, f"{label}: expected {expected}, got {actual}"


def make_sim(*, weapon_id: str = "discord", rank: int = 5) -> Simulation:
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_test_party",
        build_profile_overrides={
            "aemeath": "aemeath_user_real_01",
            "mornye": "mornye_user_real_01",
        },
    )
    sim.state.active_character_id = "mornye"
    sim.state.concerto_energy["mornye"] = 0.0
    sim.state.character_states.setdefault("mornye", {})["concerto_energy"] = 0.0
    sync_concerto_state(sim.state, "mornye")
    sim.characters["mornye"].weapon = {
        "weapon_id": weapon_id,
        "weapon_type": "broadblade",
        "rank": rank,
        "static_stats_already_in_profile": True,
    }
    return sim


def execute_skill(sim: Simulation):
    sim.state.active_character_id = "mornye"
    sim.state.cooldowns.clear()
    assert sim.execute_action("mornye_resonance_skill")
    return sim.timeline[-1]


def test_starfield_r1_restore_and_cooldown() -> None:
    sim = make_sim(weapon_id="starfield_calibrator", rank=1)
    resonance_before = sim.state.resonance_energy["mornye"]
    row = execute_skill(sim)
    assert row.weapon_effect_triggered is True
    assert row.weapon_id == "starfield_calibrator"
    assert row.weapon_rank == 1
    assert row.weapon_effect_id == "resonance_skill_concerto_restore"
    assert row.weapon_effect_resource == "concerto_energy"
    assert row.weapon_effect_source_status == "user_supplied_weapon_tooltip"
    assert row.weapon_effect_logs
    assert all("weapon_effect_source_status" in log for log in row.weapon_effect_logs)
    assert all("source_status" not in log for log in row.weapon_effect_logs)
    assert_close(row.concerto_energy_restored_by_weapon, 8.0, "Starfield R1 restore")
    assert_close(row.weapon_effect_cooldown_seconds, 20.0, "Starfield cooldown")
    assert sim.state.resonance_energy["mornye"] == resonance_before

    row = execute_skill(sim)
    assert row.weapon_effect_cooldown_blocked is True
    assert_close(row.concerto_energy_restored_by_weapon, 0.0, "blocked restore")

    while sim.state.weapon_effect_cooldowns:
        assert sim.execute_action("short_wait")
    row = execute_skill(sim)
    assert row.weapon_effect_triggered is True
    assert_close(row.concerto_energy_restored_by_weapon, 8.0, "restore after cooldown")


def test_discord_and_rank_scaling() -> None:
    discord = make_sim(weapon_id="discord", rank=1)
    row = execute_skill(discord)
    assert row.weapon_id == "discord"
    assert row.weapon_rank == 1
    assert row.weapon_effect_source_status == "user_supplied_weapon_tooltip"
    assert_close(row.concerto_energy_restored_by_weapon, 8.0, "Discord R1 restore")

    rank5 = make_sim(weapon_id="discord", rank=5)
    row = execute_skill(rank5)
    assert row.weapon_id == "discord"
    assert row.weapon_rank == 5
    assert_close(row.concerto_energy_restored_by_weapon, 16.0, "Discord R5 restore")
    assert_close(row.weapon_effect_cooldown_seconds, 20.0, "Discord cooldown")


def test_non_resonance_skill_does_not_trigger() -> None:
    sim = make_sim()
    assert sim.execute_action("mornye_basic_attack")
    row = sim.timeline[-1]
    assert row.weapon_effect_triggered is False
    assert row.concerto_energy_restored_by_weapon == 0.0


def main() -> None:
    test_starfield_r1_restore_and_cooldown()
    test_discord_and_rank_scaling()
    test_non_resonance_skill_does_not_trigger()
    print("weapon_concerto_restore_smoke_test ok")


if __name__ == "__main__":
    main()
