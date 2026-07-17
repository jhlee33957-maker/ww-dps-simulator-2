from __future__ import annotations

import copy
import hashlib
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.build_profiles import (  # noqa: E402
    load_base_build_profiles,
    load_build_profile_overlay,
    load_build_profiles,
    merge_build_profile_overlay,
)
from simulator.weapon_effects import (  # noqa: E402
    load_base_weapon_definition,
    load_weapon_definition,
    load_weapon_extension_overlay,
    merge_weapon_extension_overlay,
    resolve_weapon_rank_value,
)


DATA_DIR = ROOT / "data"
EXPECTED_BASE_BUILD_PROFILES_SHA256 = "fe0e46aaddb818ecd9b0180b3aa955671328a03c179e9dd5f8b9a7fc85506aa7"
EXPECTED_BASE_WEAPONS_SHA256 = "1e5595c9c9cb1b300d5f0e21b1f493b527f2868503511b6c1c467209b3c8df33"
ACCOUNT_IDS = {
    "aemeath": "aemeath_account_actual_01",
    "lynae": "lynae_account_actual_01",
    "mornye": "mornye_account_actual_01",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-9) -> None:
    assert math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tol), f"{label}: {actual} != {expected}"


def assert_raises(callable_obj, text: str) -> None:
    try:
        callable_obj()
    except ValueError as exc:
        assert text in str(exc), str(exc)
    else:
        raise AssertionError(f"Expected ValueError containing {text!r}")


def main() -> None:
    assert sha256(DATA_DIR / "build_profiles.json") == EXPECTED_BASE_BUILD_PROFILES_SHA256
    assert sha256(DATA_DIR / "weapons.json") == EXPECTED_BASE_WEAPONS_SHA256

    base_profiles = load_base_build_profiles(DATA_DIR)
    base_profiles_before = copy.deepcopy(base_profiles)
    overlay = load_build_profile_overlay(DATA_DIR)
    merged_profiles = merge_build_profile_overlay(base_profiles, overlay)
    assert base_profiles == base_profiles_before
    for character_id, profile_id in ACCOUNT_IDS.items():
        assert profile_id not in base_profiles["profiles"][character_id]
        profile = merged_profiles["profiles"][character_id][profile_id]
        assert profile["account_profile"] is True
        assert profile["simulation_ready"] is False
        assert "?" not in profile["display_name"]
    assert load_build_profiles(DATA_DIR)["profiles"]["lynae"]["lynae_account_actual_01"]["sequence"] == 2

    base_weapons = load_base_weapon_definition(DATA_DIR)
    base_weapons_before = copy.deepcopy(base_weapons)
    weapon_overlay = load_weapon_extension_overlay(DATA_DIR)
    merged_weapons = merge_weapon_extension_overlay(base_weapons, weapon_overlay)
    assert base_weapons == base_weapons_before
    base_static_mist = base_weapons["weapons"]["static_mist"]
    merged_static_mist = merged_weapons["weapons"]["static_mist"]
    assert "5" not in base_static_mist["rank_values"]
    assert "5" in base_static_mist["unresolved_rank_values"]
    assert_close(resolve_weapon_rank_value(merged_static_mist, 1, "incoming_atk_percent_after_outro"), 0.10, "R1")
    assert_close(resolve_weapon_rank_value(merged_static_mist, 5, "incoming_atk_percent_after_outro"), 0.20, "R5")
    assert_close(merged_static_mist["effects"]["outro_incoming_atk_buff"]["duration_seconds"], 14.0, "duration")
    assert "5" not in merged_static_mist["unresolved_rank_values"]
    for rank in (2, 3, 4):
        assert_raises(lambda rank=rank: resolve_weapon_rank_value(merged_static_mist, rank, "incoming_atk_percent_after_outro"), "unresolved")
    assert load_weapon_definition(DATA_DIR)["weapons"]["static_mist"]["rank_values"]["5"]["energy_regen_static_bonus"] == 0.256

    collision_overlay = copy.deepcopy(overlay)
    collision_overlay["profiles"]["aemeath"]["default"] = copy.deepcopy(
        overlay["profiles"]["aemeath"]["aemeath_account_actual_01"]
    )
    assert_raises(lambda: merge_build_profile_overlay(base_profiles, collision_overlay), "may not replace")

    mismatch_overlay = copy.deepcopy(overlay)
    mismatch_overlay["profiles"]["aemeath"]["aemeath_account_actual_01"]["character_id"] = "lynae"
    assert_raises(lambda: merge_build_profile_overlay(base_profiles, mismatch_overlay), "declares character")

    unknown_weapon_overlay = {"schema_version": 1, "weapon_extensions": {"unknown_weapon": {"rank_values": {"5": {}}}}}
    assert_raises(lambda: merge_weapon_extension_overlay(base_weapons, unknown_weapon_overlay), "unknown weapon")

    rank_replacement_overlay = {
        "schema_version": 1,
        "weapon_extensions": {"static_mist": {"rank_values": {"1": {"incoming_atk_percent_after_outro": 0.2}}}},
    }
    assert_raises(lambda: merge_weapon_extension_overlay(base_weapons, rank_replacement_overlay), "may not replace")

    metadata_replacement_overlay = {
        "schema_version": 1,
        "weapon_extensions": {"static_mist": {"effects": {}, "rank_values": {"5": {}}}},
    }
    assert_raises(lambda: merge_weapon_extension_overlay(base_weapons, metadata_replacement_overlay), "rank values only")

    print("user_account_actual_v120_overlay_merge_smoke_test ok")


if __name__ == "__main__":
    main()
