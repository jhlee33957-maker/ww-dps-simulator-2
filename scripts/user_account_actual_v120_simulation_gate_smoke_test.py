from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_profile_gate import AccountProfileSimulationBlocked
from simulator.account_constellation_effects import ACCOUNT_SCOPE_ID
from simulator.simulation import Simulation


DATA_DIR = ROOT / "data"
ACCOUNT_PROFILES = {
    "aemeath": ("aemeath_account_actual_01", 6, "S1-S6"),
    "lynae": ("lynae_account_actual_01", 2, "S1-S2"),
    "mornye": ("mornye_account_actual_01", 3, "S1-S3"),
}
ENTRY_POINTS = [
    "simulator execution",
    "diagnostic route replay",
    "manual baseline evaluation",
    "BC demonstration generation",
    "BC/PPO training",
    "PPO evaluation",
    "Beam Search",
    "MCTS",
]


def assert_blocked(callable_obj, *, character_id: str, profile_id: str, sequence: int, contract: str) -> None:
    try:
        callable_obj()
    except AccountProfileSimulationBlocked as exc:
        text = str(exc)
        assert profile_id in text
        assert character_id.capitalize() in text or character_id in text
        assert f"Sequence {sequence}" in text
        assert "single_persistent_boss_no_kill_no_survival" in text or "precombat_elapsed_seconds" in text
    else:
        raise AssertionError(f"{profile_id} unexpectedly passed simulation gate")


def main() -> None:
    for character_id, (profile_id, sequence, contract) in ACCOUNT_PROFILES.items():
        sim = Simulation.from_json(
            DATA_DIR,
            selected_character_ids=[character_id],
            build_profile_overrides={character_id: profile_id},
            initial_active_character=character_id,
        )
        character = sim.characters[character_id]
        assert character.account_profile is True
        assert character.simulation_ready is True
        assert character.sequence == sequence
        assert character.constellation["mechanics_implemented"] is True
        assert character.account_display_stats
        assert sim.account_profile_gate_errors
        assert sim.valid_action_ids() == []
        assert_blocked(
            lambda sim=sim: sim.execute_action("short_wait"),
            character_id=character_id,
            profile_id=profile_id,
            sequence=sequence,
            contract=contract,
        )
        for entry_point in ENTRY_POINTS:
            assert_blocked(
                lambda sim=sim, entry_point=entry_point: sim.validate_simulation_readiness(entry_point=entry_point),
                character_id=character_id,
                profile_id=profile_id,
                sequence=sequence,
                contract=contract,
            )

        scoped = Simulation.from_json(
            DATA_DIR,
            selected_character_ids=[character_id],
            build_profile_overrides={character_id: profile_id},
            initial_active_character=character_id,
            account_simulation_scope=ACCOUNT_SCOPE_ID,
            precombat_elapsed_seconds=0,
        )
        if character_id == "aemeath":
            scoped.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
        assert not scoped.account_profile_gate_errors
        assert scoped.valid_action_ids()
        assert scoped.account_constellation_state is not None

    benchmark = Simulation.from_json(DATA_DIR, party="aemeath_mornye_lynae_enabled_test_party", initial_active_character="mornye")
    assert not benchmark.account_profile_gate_errors
    assert benchmark.valid_action_ids()
    assert benchmark.execute_action("mornye_heavy_attack") is True

    print("user_account_actual_v120_simulation_gate_smoke_test ok")


if __name__ == "__main__":
    main()
