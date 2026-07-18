from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.account_config_contract import (
    ACCOUNT_PARTY_ID,
    load_account_content_start,
    validate_account_config_manifest,
    validate_content_start,
)
from simulator.roster import read_party_presets
from simulator.simulation import Simulation


def dry_validate_account_party(project_root: Path | str, party_id: str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    if party_id != ACCOUNT_PARTY_ID:
        raise ValueError(f"unsupported account party: {party_id}")
    presets = read_party_presets(root / "data")
    party = presets.get(party_id)
    if party is None:
        raise ValueError(f"account party is not available: {party_id}")
    content = validate_content_start(load_account_content_start(root))
    manifest = validate_account_config_manifest(root)
    simulation = Simulation.from_json(root / "data", selected_character_ids=party_id)
    assert simulation.state.combat_time == 0.0
    assert simulation.state.current_time == 0.0
    assert simulation.state.total_damage == 0.0
    assert simulation.initial_active_character == "mornye"
    assert simulation.state.active_character_id == "mornye"
    account = simulation.account_constellation_state or {}
    runtime = simulation.state.character_mechanics_state
    aemeath_runtime = runtime.get("aemeath") or {}
    lynae_runtime = runtime.get("lynae") or {}
    mechanic_config = simulation.state.mechanics_config
    aemeath_mode = ((mechanic_config.get("aemeath") or {}).get("aemeath_resonance_mode"))
    if aemeath_mode != "tune_rupture":
        raise ValueError("account party did not resolve Aemeath Tune Rupture mode")
    if not bool(aemeath_runtime.get("account_radiance_quick_charge_ready")):
        raise ValueError("account precombat state did not initialize Aemeath Radiance")
    if not bool((account.get("aemeath") or {}).get("radiance_quick_charge_ready")):
        raise ValueError("account constellation state did not record Aemeath Radiance")
    if float(lynae_runtime.get("overflow", 0.0)) != 120.0:
        raise ValueError("account precombat state did not restore Lynae Overflow")
    if float((account.get("lynae") or {}).get("overflow_restored_precombat", 0.0)) != 120.0:
        raise ValueError("account constellation state did not record Lynae Overflow")
    if not bool((account.get("lynae") or {}).get("optical_sampling_active_precombat")):
        raise ValueError("account precombat state did not preserve Lynae Optical Sampling")

    profile_data = {
        character_id: {
            "profile_id": simulation.active_build_profiles[character_id],
            "weapon_id": (simulation.characters[character_id].weapon or {}).get("weapon_id"),
            "weapon_rank": (simulation.characters[character_id].weapon or {}).get("rank"),
            "sequence": simulation.characters[character_id].sequence,
        }
        for character_id in party["members"]
    }
    return {
        "party_id": party_id,
        "members": list(party["members"]),
        "profiles": profile_data,
        "initial_active_character": simulation.initial_active_character,
        "scope_id": (account.get("scope") or {}).get("scope_id"),
        "precombat_elapsed_seconds": simulation.precombat_elapsed_seconds,
        "aemeath_resonance_mode": aemeath_mode,
        "aemeath_radiance_quick_charge_ready": True,
        "lynae_optical_sampling_active": True,
        "lynae_overflow_initial_gain": 120,
        "observation_version": simulation.account_observation_metadata()["observation_version"],
        "observation_shape": simulation.account_observation_metadata()["observation_shape"],
        "account_config_hash": manifest["account_config_hash"],
        "unsupported_effects": list(account.get("unsupported_effects") or []),
        "combat_time": simulation.state.combat_time,
        "current_elapsed_action_time": simulation.state.current_time,
        "action_execution_count": len(simulation.timeline),
        "content": content["content"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the candidate-122 account party without executing an action.")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--party", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("--dry-run is required; this validator never executes a route or action")
    print(json.dumps(dry_validate_account_party(args.project_root, args.party), ensure_ascii=True, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
