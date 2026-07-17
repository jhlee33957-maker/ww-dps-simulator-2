from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import load_build_profiles
from simulator.weapon_effects import load_weapon_definition, resolve_weapon_rank_value


DATA_DIR = ROOT / "data"


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tol), f"{label}: {actual} != {expected}"


def main() -> None:
    data = load_weapon_definition(DATA_DIR)
    static_mist = data["weapons"]["static_mist"]
    effect = static_mist["effects"]["outro_incoming_atk_buff"]

    assert_close(resolve_weapon_rank_value(static_mist, 1, "incoming_atk_percent_after_outro"), 0.10, "R1 incoming ATK")
    assert_close(resolve_weapon_rank_value(static_mist, 5, "incoming_atk_percent_after_outro"), 0.20, "R5 incoming ATK")
    assert_close(effect["duration_seconds"], 14.0, "Static Mist duration")
    assert_close(resolve_weapon_rank_value(static_mist, 5, "energy_regen_static_bonus"), 0.256, "R5 static ER")

    for rank in (2, 3, 4):
        try:
            resolve_weapon_rank_value(static_mist, rank, "incoming_atk_percent_after_outro")
        except ValueError as exc:
            assert "unresolved" in str(exc) and "silent zero" in str(exc)
        else:
            raise AssertionError(f"Static Mist rank {rank} unexpectedly resolved")

    fixed_account_r5_result = 0.10
    assert resolve_weapon_rank_value(static_mist, 5, "incoming_atk_percent_after_outro") != fixed_account_r5_result

    profiles = load_build_profiles(DATA_DIR)["profiles"]
    lynae_account = profiles["lynae"]["lynae_account_actual_01"]
    assert_close(lynae_account["combat_stats"]["energy_regen"], 1.548, "Lynae account ER")
    assert not math.isclose(lynae_account["combat_stats"]["energy_regen"], 1.548 + 0.256, rel_tol=0.0, abs_tol=1e-9)

    print("static_mist_r5_rank_resolution_smoke_test ok")


if __name__ == "__main__":
    main()
