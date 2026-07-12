from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "manual_120s_bc_demonstration_v1"
SOURCE_VERIFIED_BASELINE_LABEL = "105"
CANDIDATE_LABEL = "106"
ROUTE_ID = "manual_120s_primary_v105"
EPISODE_ID = "manual_120s_primary_v105_ep0000"
ROUTE_FILE = Path("data/manual_120s_baseline_routes_v104.json")
SOURCE_ROUTE_FILE_SHA256 = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"
PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
INITIAL_ACTIVE_CHARACTER = "aemeath"
CURRICULUM_RESET_MODE = "none"
OBSERVATION_VERSION = "slot_generic_mechanics_v5"
OBSERVATION_SHAPE = (314,)
POLICY_ACTION_COUNT = 25
MAX_POLICY_ACTION_SLOTS = 32
SAMPLE_COUNT = 148
FINAL_COMBAT_TIME = 120.0
TOTAL_DAMAGE = 5165134.682363359
DPS = 43042.78901969466
REWARD_FORMULA = "damage_this_action / 10000.0"
DIRECT_ACTION_MANIFEST_SHA256 = "ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d"
SELECTED_SEQUENCE_SHA256 = "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
RESOLVED_SEQUENCE_SHA256 = "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
DEFAULT_DEMO_PATH = PROJECT_ROOT / "data" / "generated" / "manual_120s_bc_demonstration_v105.npz"

ACTION_DATA_HASH_FILES = (
    Path("data/actions.json"),
    Path("data/transition_actions.json"),
    Path("data/tune_responses.json"),
)

PARTY_CONFIG_HASH_FILES = (
    Path("data/party_presets.json"),
    Path("data/build_profiles.json"),
    Path("data/transition_config.json"),
    Path("data/characters.json"),
    Path("data/weapons.json"),
    Path("data/buffs.json"),
)

REQUIRED_ARRAYS = (
    "observations",
    "action_indices",
    "action_ids",
    "action_masks",
    "resolved_action_ids",
    "active_characters",
    "rewards",
    "damages",
    "combat_time_costs",
    "combat_times_before",
    "combat_times_after",
    "action_times_before",
    "action_times_after",
    "episode_ids",
    "step_indices",
    "terminated",
    "truncated",
    "remaining_returns",
    "remaining_damage",
    "observation_versions",
    "action_data_hashes",
    "party_config_hashes",
    "route_ids",
    "metadata_json",
)

LEGACY_DEMO_PATHS = (
    PROJECT_ROOT / "data" / "generated" / "route_demonstrations_aemeath_mornye_lynae.npz",
    PROJECT_ROOT / "data" / "generated" / "route_demonstrations_aemeath_mornye_lynae_v2.npz",
)


class DemoContractError(ValueError):
    pass


def canonical_json_bundle_hash(paths: tuple[Path, ...] | list[Path], *, root: Path = PROJECT_ROOT) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted((Path(path) for path in paths), key=lambda item: item.as_posix()):
        path = root / rel_path
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest.update(rel_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(canonical)
        digest.update(b"\0")
    return digest.hexdigest()


def action_data_hash(*, root: Path = PROJECT_ROOT) -> str:
    return canonical_json_bundle_hash(ACTION_DATA_HASH_FILES, root=root)


def party_config_hash(*, root: Path = PROJECT_ROOT) -> str:
    return canonical_json_bundle_hash(PARTY_CONFIG_HASH_FILES, root=root)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_relative_posix(path: Path, *, root: Path = PROJECT_ROOT) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(json_safe(key)): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return project_relative_posix(value)
    return value


def sequence_hash(sequence: list[str] | np.ndarray) -> str:
    payload = json.dumps([str(item) for item in sequence], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_route_primary(*, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    route_data = json.loads((root / ROUTE_FILE).read_text(encoding="utf-8-sig"))
    return route_data["routes"]["primary"]


def load_demo_npz(path: Path = DEFAULT_DEMO_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Demo file not found: {path}")
    payload: dict[str, Any] = {"path": path}
    with np.load(path, allow_pickle=False) as data:
        for name in data.files:
            payload[name] = np.asarray(data[name])
    if "metadata_json" not in payload:
        raise DemoContractError("Demo missing required field metadata_json")
    payload["metadata"] = json.loads(_scalar_string(payload["metadata_json"]))
    return payload


def array_manifest(demo: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        name: {"dtype": str(np.asarray(demo[name]).dtype), "shape": list(np.asarray(demo[name]).shape)}
        for name in REQUIRED_ARRAYS
        if name in demo
    }


def validate_demo_contract(
    demo: dict[str, Any],
    env: Any,
    *,
    root: Path = PROJECT_ROOT,
    require_replay_ready: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    missing = [name for name in REQUIRED_ARRAYS if name not in demo]
    if missing:
        raise DemoContractError(f"Demo missing required fields: {missing}")

    metadata = demo["metadata"]
    observations = np.asarray(demo["observations"])
    action_indices = np.asarray(demo["action_indices"])
    action_ids = np.asarray(demo["action_ids"], dtype=str)
    action_masks = np.asarray(demo["action_masks"])
    row_count = len(action_indices)
    policy_action_ids = list(metadata.get("policy_action_ids") or [])
    current_action_ids = list(env.get_policy_action_ids())
    current_observation_meta = env.observation_metadata()

    for name in REQUIRED_ARRAYS:
        if name == "metadata_json":
            continue
        array = np.asarray(demo[name])
        if array.shape[:1] != (row_count,):
            errors.append(f"{name} row count {array.shape[:1]} does not match action_indices row count {row_count}")

    if row_count != SAMPLE_COUNT:
        errors.append(f"sample_count mismatch: actual {row_count}, expected {SAMPLE_COUNT}")
    if observations.shape != (SAMPLE_COUNT, *OBSERVATION_SHAPE):
        errors.append(f"observation shape mismatch: actual {list(observations.shape)}, expected {[SAMPLE_COUNT, *OBSERVATION_SHAPE]}")
    if action_masks.shape != (SAMPLE_COUNT, POLICY_ACTION_COUNT):
        errors.append(f"action mask shape mismatch: actual {list(action_masks.shape)}, expected {[SAMPLE_COUNT, POLICY_ACTION_COUNT]}")
    if observations.dtype != np.float32:
        errors.append(f"observations dtype mismatch: actual {observations.dtype}, expected float32")
    if action_indices.dtype != np.int64:
        errors.append(f"action_indices dtype mismatch: actual {action_indices.dtype}, expected int64")
    if action_masks.dtype != np.bool_:
        errors.append(f"action_masks dtype mismatch: actual {action_masks.dtype}, expected bool")

    if current_observation_meta.get("observation_version") != OBSERVATION_VERSION:
        errors.append(
            f"env observation version mismatch: actual {current_observation_meta.get('observation_version')}, expected {OBSERVATION_VERSION}"
        )
    if list(env.observation_space.shape) != list(OBSERVATION_SHAPE):
        errors.append(f"env observation shape mismatch: actual {list(env.observation_space.shape)}, expected {list(OBSERVATION_SHAPE)}")
    if env.action_space.n != POLICY_ACTION_COUNT:
        errors.append(f"env policy action count mismatch: actual {env.action_space.n}, expected {POLICY_ACTION_COUNT}")
    if current_action_ids != policy_action_ids:
        errors.append("metadata policy_action_ids do not match current env policy action order")

    expected_metadata = {
        "schema_version": SCHEMA_VERSION,
        "source_verified_baseline_label": SOURCE_VERIFIED_BASELINE_LABEL,
        "candidate_label": CANDIDATE_LABEL,
        "route_id": ROUTE_ID,
        "source_route_file": ROUTE_FILE.as_posix(),
        "party_id": PARTY_ID,
        "initial_active_character": INITIAL_ACTIVE_CHARACTER,
        "curriculum_reset_mode": CURRICULUM_RESET_MODE,
        "episode_count": 1,
        "sample_count": SAMPLE_COUNT,
        "observation_version": OBSERVATION_VERSION,
        "observation_shape": list(OBSERVATION_SHAPE),
        "policy_action_count": POLICY_ACTION_COUNT,
        "max_policy_action_slots": MAX_POLICY_ACTION_SLOTS,
        "selected_sequence_sha256": SELECTED_SEQUENCE_SHA256,
        "resolved_sequence_sha256": RESOLVED_SEQUENCE_SHA256,
        "final_combat_time": FINAL_COMBAT_TIME,
        "total_damage": TOTAL_DAMAGE,
        "dps": DPS,
        "reward_formula": REWARD_FORMULA,
        "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
        "no_character_specific_usage_reward_bonus": True,
        "reward_shaping": False,
        "future_information_used_as_policy_input": False,
        "training_only": True,
        "global_optimum_claimed": False,
        "human_authored_route": True,
    }
    for key, expected in expected_metadata.items():
        if metadata.get(key) != expected:
            errors.append(f"metadata {key} mismatch: actual {metadata.get(key)!r}, expected {expected!r}")

    expected_action_hash = action_data_hash(root=root)
    expected_party_hash = party_config_hash(root=root)
    route_sha = file_sha256(root / ROUTE_FILE)
    if metadata.get("action_data_hash") != expected_action_hash:
        errors.append("metadata action_data_hash does not match current repository")
    if metadata.get("party_config_hash") != expected_party_hash:
        errors.append("metadata party_config_hash does not match current repository")
    if route_sha != SOURCE_ROUTE_FILE_SHA256:
        errors.append(f"current route file raw SHA mismatch: actual {route_sha}, expected {SOURCE_ROUTE_FILE_SHA256}")
    if metadata.get("source_route_file_sha256") != route_sha:
        errors.append("metadata source_route_file_sha256 does not match current route file")
    if set(map(str, np.asarray(demo["action_data_hashes"], dtype=str))) != {expected_action_hash}:
        errors.append("sample-level action_data_hashes do not all match current repository")
    if set(map(str, np.asarray(demo["party_config_hashes"], dtype=str))) != {expected_party_hash}:
        errors.append("sample-level party_config_hashes do not all match current repository")
    if set(map(str, np.asarray(demo["observation_versions"], dtype=str))) != {OBSERVATION_VERSION}:
        errors.append("sample-level observation_versions mismatch")
    if set(map(str, np.asarray(demo["route_ids"], dtype=str))) != {ROUTE_ID}:
        errors.append("sample-level route_ids mismatch")
    if set(map(str, np.asarray(demo["episode_ids"], dtype=str))) != {EPISODE_ID}:
        errors.append("episode_ids mismatch")

    if np.any(action_indices < 0) or np.any(action_indices >= POLICY_ACTION_COUNT):
        errors.append("action_indices contain out-of-range values")
    invalid_rows = [
        int(index)
        for index, action_index in enumerate(action_indices)
        if 0 <= int(action_index) < action_masks.shape[1] and not bool(action_masks[index, int(action_index)])
    ]
    if invalid_rows:
        errors.append(f"selected actions are invalid under stored masks at rows {invalid_rows[:20]}")
    mismatched_action_ids = [
        int(index)
        for index, action_index in enumerate(action_indices)
        if 0 <= int(action_index) < len(policy_action_ids) and str(action_ids[index]) != policy_action_ids[int(action_index)]
    ]
    if mismatched_action_ids:
        errors.append(f"action_ids do not match action_indices at rows {mismatched_action_ids[:20]}")

    step_indices = np.asarray(demo["step_indices"], dtype=np.int64)
    if not np.array_equal(step_indices, np.arange(SAMPLE_COUNT, dtype=np.int64)):
        errors.append("step_indices are not exactly 0..147")
    terminated = np.asarray(demo["terminated"], dtype=bool)
    truncated = np.asarray(demo["truncated"], dtype=bool)
    if not np.array_equal(terminated, np.asarray([False] * (SAMPLE_COUNT - 1) + [True], dtype=bool)):
        errors.append("terminated flags must be false except the final sample")
    if np.any(truncated):
        errors.append("truncated flags must all be false")

    numeric_fields = (
        "observations",
        "rewards",
        "damages",
        "combat_time_costs",
        "combat_times_before",
        "combat_times_after",
        "action_times_before",
        "action_times_after",
        "remaining_returns",
        "remaining_damage",
    )
    for name in numeric_fields:
        if not np.all(np.isfinite(np.asarray(demo[name], dtype=np.float64))):
            errors.append(f"{name} contains non-finite values")

    rewards = np.asarray(demo["rewards"], dtype=np.float64)
    damages = np.asarray(demo["damages"], dtype=np.float64)
    expected_returns = reverse_cumulative(rewards)
    expected_damage = reverse_cumulative(damages)
    if not np.allclose(np.asarray(demo["remaining_returns"], dtype=np.float64), expected_returns, rtol=0.0, atol=1e-9):
        errors.append("remaining_returns do not match inclusive reverse cumulative rewards")
    if not np.allclose(np.asarray(demo["remaining_damage"], dtype=np.float64), expected_damage, rtol=0.0, atol=1e-9):
        errors.append("remaining_damage does not match inclusive reverse cumulative damages")
    if sequence_hash(action_ids.tolist()) != SELECTED_SEQUENCE_SHA256:
        errors.append("selected action sequence hash mismatch")
    if sequence_hash(np.asarray(demo["resolved_action_ids"], dtype=str).tolist()) != RESOLVED_SEQUENCE_SHA256:
        errors.append("resolved action sequence hash mismatch")

    total_reward = float(math.fsum(float(value) for value in rewards))
    total_damage = float(math.fsum(float(value) for value in damages))
    final_time = float(np.asarray(demo["combat_times_after"], dtype=np.float64)[-1])
    if abs(total_damage - TOTAL_DAMAGE) > 1e-8:
        errors.append(f"total damage mismatch: actual {total_damage}, expected {TOTAL_DAMAGE}")
    if abs(final_time - FINAL_COMBAT_TIME) > 1e-9:
        errors.append(f"final combat time mismatch: actual {final_time}, expected {FINAL_COMBAT_TIME}")
    if abs(metadata.get("total_reward", float("nan")) - total_reward) > 1e-9:
        errors.append("metadata total_reward does not match recomputed rewards")
    if abs(metadata.get("total_damage", float("nan")) - total_damage) > 1e-8:
        errors.append("metadata total_damage does not match recomputed damages")
    if abs(metadata.get("dps", float("nan")) - (total_damage / FINAL_COMBAT_TIME)) > 1e-9:
        errors.append("metadata DPS does not match recomputed total_damage/final_time")
    if require_replay_ready and list(policy_action_ids) != current_action_ids:
        errors.append("demo is not replay-ready because env action IDs differ from metadata")

    if errors:
        raise DemoContractError("Manual 120s BC demo contract failed:\n- " + "\n- ".join(errors))

    return {
        "status": "ok",
        "sample_count": row_count,
        "total_reward": float(metadata.get("total_reward", total_reward)),
        "raw_reward_delta_sum": total_reward,
        "total_damage": float(metadata.get("total_damage", TOTAL_DAMAGE)),
        "raw_damage_delta_sum": total_damage,
        "final_combat_time": final_time,
        "action_data_hash": expected_action_hash,
        "party_config_hash": expected_party_hash,
        "source_route_file_sha256": route_sha,
    }


def validate_legacy_demo_rejected(path: Path, *, expected_shape: tuple[int, ...] = OBSERVATION_SHAPE) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as data:
        observation_shape = tuple(np.asarray(data["observations"]).shape[1:])
        action_count = int(np.asarray(data["action_masks"]).shape[1])
    if observation_shape == expected_shape and action_count == POLICY_ACTION_COUNT:
        raise DemoContractError(f"Legacy demo unexpectedly matches current contract: {path}")
    display_path = project_relative_posix(path)
    message = (
        f"incompatible legacy BC demo {display_path}: actual observation shape {list(observation_shape)} "
        f"and action count {action_count}; expected observation shape {list(expected_shape)} "
        f"and action count {POLICY_ACTION_COUNT}"
    )
    return {
        "path": display_path,
        "status": "rejected",
        "actual_observation_shape": list(observation_shape),
        "actual_action_count": action_count,
        "expected_observation_shape": list(expected_shape),
        "expected_action_count": POLICY_ACTION_COUNT,
        "message": message,
    }


def replay_validate_demo(demo: dict[str, Any], env_factory: Any) -> dict[str, Any]:
    env = env_factory()
    observation, _info = env.reset(seed=0)
    invalid_actions: list[dict[str, Any]] = []
    short_wait_substitutions: list[int] = []
    mismatches: list[str] = []
    selected: list[str] = []
    resolved: list[str] = []
    accumulated_damage_deltas = 0.0
    policy_action_ids = env.get_policy_action_ids()

    for index in range(SAMPLE_COUNT):
        expected_obs = np.asarray(demo["observations"][index], dtype=np.float32)
        expected_mask = np.asarray(demo["action_masks"][index], dtype=bool)
        current_mask = np.asarray(env.action_masks(), dtype=bool)
        if not np.array_equal(np.asarray(observation, dtype=np.float32), expected_obs):
            mismatches.append(f"row {index}: pre-action observation mismatch")
        if not np.array_equal(current_mask, expected_mask):
            mismatches.append(f"row {index}: pre-action action mask mismatch")
        action_index = int(np.asarray(demo["action_indices"], dtype=np.int64)[index])
        action_id = str(np.asarray(demo["action_ids"], dtype=str)[index])
        if policy_action_ids[action_index] != action_id:
            mismatches.append(f"row {index}: action index/id mismatch")
        if not bool(current_mask[action_index]):
            invalid_actions.append({"row": index, "action_index": action_index, "action_id": action_id})
        active_before = env.simulation.state.active_character_id
        combat_before = float(env.simulation.state.combat_time)
        action_before = float(env.simulation.state.current_time)
        observation, reward, terminated, truncated, info = env.step(action_index)
        if info.get("invalid_action"):
            invalid_actions.append({"row": index, "action_index": action_index, "action_id": action_id, "env_info": info})
        if action_id == "short_wait" or info.get("action_id") == "short_wait":
            short_wait_substitutions.append(index)
        damage = float(info["damage_this_action"])
        accumulated_damage_deltas += damage
        resolved_id = str(info["resolved_action_id"])
        selected.append(action_id)
        resolved.append(resolved_id)
        comparisons = {
            "resolved_action_id": (resolved_id, str(np.asarray(demo["resolved_action_ids"], dtype=str)[index]), None),
            "active_character": (active_before, str(np.asarray(demo["active_characters"], dtype=str)[index]), None),
            "reward": (float(reward), float(np.asarray(demo["rewards"], dtype=np.float64)[index]), 1e-9),
            "damage": (damage, float(np.asarray(demo["damages"], dtype=np.float64)[index]), 1e-9),
            "combat_time_before": (combat_before, float(np.asarray(demo["combat_times_before"], dtype=np.float64)[index]), 1e-9),
            "combat_time_after": (float(env.simulation.state.combat_time), float(np.asarray(demo["combat_times_after"], dtype=np.float64)[index]), 1e-9),
            "action_time_before": (action_before, float(np.asarray(demo["action_times_before"], dtype=np.float64)[index]), 1e-9),
            "action_time_after": (float(env.simulation.state.current_time), float(np.asarray(demo["action_times_after"], dtype=np.float64)[index]), 1e-9),
            "terminated": (bool(terminated), bool(np.asarray(demo["terminated"], dtype=bool)[index]), None),
            "truncated": (bool(truncated), bool(np.asarray(demo["truncated"], dtype=bool)[index]), None),
        }
        for label, (actual, expected, tolerance) in comparisons.items():
            if tolerance is None:
                if actual != expected:
                    mismatches.append(f"row {index}: {label} actual {actual!r} expected {expected!r}")
            elif abs(float(actual) - float(expected)) > tolerance:
                mismatches.append(f"row {index}: {label} actual {actual!r} expected {expected!r}")

    selected_hash = sequence_hash(selected)
    resolved_hash = sequence_hash(resolved)
    if abs(float(env.simulation.state.combat_time) - FINAL_COMBAT_TIME) > 1e-9:
        mismatches.append("final combat_time mismatch")
    final_total_damage = float(env.simulation.state.total_damage)
    if abs(final_total_damage - TOTAL_DAMAGE) > 1e-8:
        mismatches.append("total damage mismatch")
    if abs(accumulated_damage_deltas - TOTAL_DAMAGE) > 1e-8:
        mismatches.append("accumulated per-row damage delta sum mismatch")
    if selected_hash != SELECTED_SEQUENCE_SHA256:
        mismatches.append("selected sequence hash mismatch")
    if resolved_hash != RESOLVED_SEQUENCE_SHA256:
        mismatches.append("resolved sequence hash mismatch")
    if invalid_actions:
        mismatches.append(f"invalid actions encountered: {invalid_actions[:5]}")
    if short_wait_substitutions:
        mismatches.append(f"short_wait substitutions/actions encountered at rows: {short_wait_substitutions}")

    if mismatches:
        raise DemoContractError("Manual 120s BC demo replay failed:\n- " + "\n- ".join(mismatches[:50]))
    return {
        "status": "ok",
        "sample_count": SAMPLE_COUNT,
        "final_combat_time": float(env.simulation.state.combat_time),
        "total_damage": TOTAL_DAMAGE,
        "raw_env_total_damage": final_total_damage,
        "accumulated_damage_delta_sum": accumulated_damage_deltas,
        "selected_sequence_sha256": selected_hash,
        "resolved_sequence_sha256": resolved_hash,
        "invalid_action_count": len(invalid_actions),
        "short_wait_substitution_count": len(short_wait_substitutions),
        "placeholder_fallback": {
            "count": 1,
            "step": 6,
            "selected_action_id": "swap_to_mornye",
        },
    }


def alias_audit(demo: dict[str, Any]) -> dict[str, Any]:
    buckets: dict[bytes, list[tuple[int, int, str]]] = defaultdict(list)
    observations = np.asarray(demo["observations"], dtype=np.float32)
    masks = np.asarray(demo["action_masks"], dtype=bool)
    actions = np.asarray(demo["action_indices"], dtype=np.int64)
    action_ids = np.asarray(demo["action_ids"], dtype=str)
    for index in range(len(actions)):
        key = observations[index].tobytes() + masks[index].tobytes()
        buckets[key].append((index, int(actions[index]), str(action_ids[index])))
    conflicts = []
    for rows in buckets.values():
        target_indices = {row[1] for row in rows}
        if len(target_indices) > 1:
            conflicts.append(
                {
                    "rows": [row[0] for row in rows],
                    "target_action_indices": sorted(target_indices),
                    "target_action_ids": sorted({row[2] for row in rows}),
                }
            )
    if conflicts:
        raise DemoContractError(f"Observation alias conflicts found: {json.dumps(conflicts, indent=2)}")
    return {
        "status": "ok",
        "unique_observation_mask_keys": len(buckets),
        "conflicting_target_key_count": 0,
        "conflicts": [],
    }


def reverse_cumulative(values: np.ndarray) -> np.ndarray:
    return np.cumsum(np.asarray(values, dtype=np.float64)[::-1], dtype=np.float64)[::-1]


def _scalar_string(value: Any) -> str:
    array = np.asarray(value)
    if array.shape == ():
        return str(array.item())
    if array.shape == (1,):
        return str(array[0])
    return str(value)


def distribution(values: np.ndarray | list[str]) -> dict[str, int]:
    return dict(Counter(map(str, values)))
