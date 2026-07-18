from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ACCOUNT_CONFIG_COMPONENT_PATHS = (
    "data/account_build_profiles_v120.json",
    "data/account_weapon_extensions_v120.json",
    "data/account_constellation_mechanics_v121.json",
    "data/account_simulation_scope_v121.json",
    "data/account_party_presets_v122.json",
    "data/account_content_start_v122.json",
)
ACCOUNT_CONFIG_MANIFEST_PATH = "data/account_config_manifest_v122.json"
ACCOUNT_PARTY_ID = "aemeath_mornye_lynae_account_actual_01"
ACCOUNT_OBSERVATION_VERSION = "slot_account_constellation_single_boss_v6"
ACCOUNT_OBSERVATION_SHAPE = 330
POLICY_ACTION_COUNT = 25


def project_root(root: Path | str | None = None) -> Path:
    return Path(root) if root is not None else Path(__file__).resolve().parents[1]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component_hashes(root: Path | str | None = None) -> dict[str, str]:
    base = project_root(root)
    return {relative_path: file_sha256(base / relative_path) for relative_path in ACCOUNT_CONFIG_COMPONENT_PATHS}


def account_config_hash(root: Path | str | None = None) -> str:
    payload = {
        "account_party_id": ACCOUNT_PARTY_ID,
        "components": component_hashes(root),
        "observation_version": ACCOUNT_OBSERVATION_VERSION,
        "observation_shape": ACCOUNT_OBSERVATION_SHAPE,
        "policy_action_count": POLICY_ACTION_COUNT,
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_account_config_manifest(root: Path | str | None = None) -> dict[str, Any]:
    hashes = component_hashes(root)
    return {
        "schema_version": "account_config_manifest_v122",
        "account_party_id": ACCOUNT_PARTY_ID,
        "account_config_hash": account_config_hash(root),
        "component_paths": list(ACCOUNT_CONFIG_COMPONENT_PATHS),
        "component_sha256": hashes,
        "observation_version": ACCOUNT_OBSERVATION_VERSION,
        "observation_shape": ACCOUNT_OBSERVATION_SHAPE,
        "policy_action_count": POLICY_ACTION_COUNT,
    }


def load_account_content_start(root: Path | str | None = None) -> dict[str, Any]:
    path = project_root(root) / "data/account_content_start_v122.json"
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_account_config_manifest(root: Path | str | None = None) -> dict[str, Any]:
    path = project_root(root) / ACCOUNT_CONFIG_MANIFEST_PATH
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def validate_content_start(content_start: dict[str, Any]) -> dict[str, Any]:
    if content_start.get("schema_version") != "account_content_start_v122":
        raise ValueError("unexpected account content-start schema")
    if content_start.get("party_id") != ACCOUNT_PARTY_ID:
        raise ValueError("account content-start party_id mismatch")
    if content_start.get("scope_id") != "single_persistent_boss_no_kill_no_survival":
        raise ValueError("account content-start scope mismatch")
    if content_start.get("initial_active_character") != "mornye":
        raise ValueError("account content-start initial active character mismatch")
    if content_start.get("aemeath_resonance_mode") != "tune_rupture":
        raise ValueError("account content-start must use tune_rupture")
    if float(content_start.get("precombat_elapsed_seconds", 0.0)) <= 4.0:
        raise ValueError("account content-start must satisfy the Aemeath > 4.0 precombat contract")
    if not bool(content_start.get("account_optical_sampling_active")):
        raise ValueError("account content-start requires active Lynae Optical Sampling")
    return content_start


def validate_account_config_manifest(root: Path | str | None = None) -> dict[str, Any]:
    manifest = load_account_config_manifest(root)
    expected = build_account_config_manifest(root)
    if manifest != expected:
        raise ValueError("account configuration manifest does not match its component contracts")
    validate_content_start(load_account_content_start(root))
    return manifest
