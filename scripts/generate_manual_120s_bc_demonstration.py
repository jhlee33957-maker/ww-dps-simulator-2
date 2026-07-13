from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import (
    CANDIDATE_LABEL,
    CURRICULUM_RESET_MODE,
    DEFAULT_DEMO_PATH,
    DIRECT_ACTION_MANIFEST_SHA256,
    DPS,
    EPISODE_ID,
    FINAL_COMBAT_TIME,
    INITIAL_ACTIVE_CHARACTER,
    LEGACY_DEMO_PATHS,
    MAX_POLICY_ACTION_SLOTS,
    OBSERVATION_SHAPE,
    OBSERVATION_VERSION,
    PARTY_ID,
    POLICY_ACTION_COUNT,
    REQUIRED_ARRAYS,
    RESOLVED_SEQUENCE_SHA256,
    REWARD_FORMULA,
    ROUTE_FILE,
    ROUTE_ID,
    SAMPLE_COUNT,
    SCHEMA_VERSION,
    SELECTED_SEQUENCE_SHA256,
    SOURCE_ROUTE_FILE_SHA256,
    SOURCE_VERIFIED_BASELINE_LABEL,
    TOTAL_DAMAGE,
    action_data_hash,
    alias_audit,
    array_manifest,
    distribution,
    file_sha256,
    load_demo_npz,
    load_route_primary,
    party_config_hash,
    project_relative_posix,
    replay_validate_demo,
    reverse_cumulative,
    sequence_hash,
    validate_demo_contract,
    validate_legacy_demo_rejected,
)


SUMMARY_PATH = ROOT / "results" / "manual_120s_bc_demonstration_v105_summary.json"
REPORT_PATH = ROOT / "reports" / "manual_120s_bc_demonstration_v105.md"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the canonical manual 120s BC demonstration dataset.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DEMO_PATH)
    parser.add_argument("--summary-path", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    return parser


def generate_manual_120s_bc_demonstration(output_path: Path = DEFAULT_DEMO_PATH) -> dict[str, Any]:
    route = load_route_primary(root=ROOT)
    selected_actions = [str(action_id) for action_id in route["selected_policy_actions"]]
    expected_resolved = [str(action_id) for action_id in route["expected_resolved_actions"]]
    if len(selected_actions) != SAMPLE_COUNT:
        raise RuntimeError(f"selected policy action count {len(selected_actions)} != {SAMPLE_COUNT}")
    if sequence_hash(selected_actions) != SELECTED_SEQUENCE_SHA256:
        raise RuntimeError("source route selected sequence hash does not match verified baseline 105")
    if sequence_hash(expected_resolved) != RESOLVED_SEQUENCE_SHA256:
        raise RuntimeError("source route resolved sequence hash does not match verified baseline 105")

    env = _make_env()
    observation, reset_info = env.reset(seed=0)
    if reset_info.get("curriculum_reset_mode") != CURRICULUM_RESET_MODE:
        raise RuntimeError(f"unexpected curriculum reset info: {reset_info}")
    policy_action_ids = env.get_policy_action_ids()
    if len(policy_action_ids) != POLICY_ACTION_COUNT:
        raise RuntimeError(f"policy action count {len(policy_action_ids)} != {POLICY_ACTION_COUNT}")
    if list(env.observation_space.shape) != list(OBSERVATION_SHAPE):
        raise RuntimeError(f"observation shape {env.observation_space.shape} != {OBSERVATION_SHAPE}")

    observations: list[np.ndarray] = []
    action_indices: list[int] = []
    action_ids: list[str] = []
    action_masks: list[np.ndarray] = []
    resolved_action_ids: list[str] = []
    active_characters: list[str] = []
    rewards: list[float] = []
    damages: list[float] = []
    combat_time_costs: list[float] = []
    combat_times_before: list[float] = []
    combat_times_after: list[float] = []
    action_times_before: list[float] = []
    action_times_after: list[float] = []
    terminated_values: list[bool] = []
    truncated_values: list[bool] = []

    for index, selected_action_id in enumerate(selected_actions):
        if selected_action_id not in policy_action_ids:
            raise RuntimeError(f"step {index}: selected action {selected_action_id!r} not in policy action space")
        action_index = policy_action_ids.index(selected_action_id)
        pre_observation = np.asarray(observation, dtype=np.float32)
        pre_mask = np.asarray(env.action_masks(), dtype=bool)
        if pre_observation.shape != OBSERVATION_SHAPE:
            raise RuntimeError(f"step {index}: observation shape {pre_observation.shape} != {OBSERVATION_SHAPE}")
        if pre_mask.shape != (POLICY_ACTION_COUNT,):
            raise RuntimeError(f"step {index}: action mask shape {pre_mask.shape} != {(POLICY_ACTION_COUNT,)}")
        if not bool(pre_mask[action_index]):
            raise RuntimeError(_invalid_action_message(env, index, selected_action_id, policy_action_ids, pre_mask))

        active_before = str(env.simulation.state.active_character_id)
        combat_before = float(env.simulation.state.combat_time)
        action_before = float(env.simulation.state.current_time)
        observation, reward, terminated, truncated, info = env.step(action_index)
        if info.get("invalid_action") or not info.get("valid_action"):
            raise RuntimeError(f"step {index}: env rejected action {selected_action_id!r}: {json.dumps(info, indent=2)}")
        if info.get("action_id") != selected_action_id:
            raise RuntimeError(f"step {index}: env action_id {info.get('action_id')!r} != selected {selected_action_id!r}")
        resolved_action_id = str(info["resolved_action_id"])
        if resolved_action_id != expected_resolved[index]:
            raise RuntimeError(
                f"step {index}: resolved action {resolved_action_id!r} != expected {expected_resolved[index]!r}"
            )

        observations.append(pre_observation)
        action_indices.append(action_index)
        action_ids.append(selected_action_id)
        action_masks.append(pre_mask)
        resolved_action_ids.append(resolved_action_id)
        active_characters.append(active_before)
        rewards.append(float(reward))
        damages.append(float(info["damage_this_action"]))
        combat_times_before.append(combat_before)
        combat_times_after.append(float(env.simulation.state.combat_time))
        action_times_before.append(action_before)
        action_times_after.append(float(env.simulation.state.current_time))
        combat_time_costs.append(float(env.simulation.state.combat_time) - combat_before)
        terminated_values.append(bool(terminated))
        truncated_values.append(bool(truncated))

    if not terminated_values[-1] or any(terminated_values[:-1]) or any(truncated_values):
        raise RuntimeError("termination contract failed while generating manual 120s BC demo")
    damage_delta_sum = float(math.fsum(float(value) for value in damages))
    total_damage = float(env.simulation.state.total_damage)
    total_reward = TOTAL_DAMAGE / 10000.0
    if abs(total_damage - TOTAL_DAMAGE) > 1e-8:
        raise RuntimeError(f"generated total damage {total_damage} != {TOTAL_DAMAGE}")
    if abs(damage_delta_sum - TOTAL_DAMAGE) > 1e-8:
        raise RuntimeError(f"generated damage delta sum {damage_delta_sum} != {TOTAL_DAMAGE}")
    if abs(float(env.simulation.state.combat_time) - FINAL_COMBAT_TIME) > 1e-9:
        raise RuntimeError(f"generated final combat time {env.simulation.state.combat_time} != {FINAL_COMBAT_TIME}")
    if sequence_hash(action_ids) != SELECTED_SEQUENCE_SHA256:
        raise RuntimeError("generated selected sequence hash mismatch")
    if sequence_hash(resolved_action_ids) != RESOLVED_SEQUENCE_SHA256:
        raise RuntimeError("generated resolved sequence hash mismatch")

    route_sha = file_sha256(ROOT / ROUTE_FILE)
    if route_sha != SOURCE_ROUTE_FILE_SHA256:
        raise RuntimeError(f"route raw SHA {route_sha} != expected {SOURCE_ROUTE_FILE_SHA256}")
    action_hash = action_data_hash(root=ROOT)
    party_hash = party_config_hash(root=ROOT)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "source_verified_baseline_label": SOURCE_VERIFIED_BASELINE_LABEL,
        "candidate_label": CANDIDATE_LABEL,
        "route_id": ROUTE_ID,
        "source_route_file": ROUTE_FILE.as_posix(),
        "source_route_file_sha256": route_sha,
        "party_id": PARTY_ID,
        "initial_active_character": INITIAL_ACTIVE_CHARACTER,
        "curriculum_reset_mode": CURRICULUM_RESET_MODE,
        "episode_count": 1,
        "sample_count": SAMPLE_COUNT,
        "observation_version": OBSERVATION_VERSION,
        "observation_shape": list(OBSERVATION_SHAPE),
        "policy_action_count": POLICY_ACTION_COUNT,
        "max_policy_action_slots": MAX_POLICY_ACTION_SLOTS,
        "policy_action_ids": policy_action_ids,
        "selected_sequence_sha256": SELECTED_SEQUENCE_SHA256,
        "resolved_sequence_sha256": RESOLVED_SEQUENCE_SHA256,
        "final_combat_time": FINAL_COMBAT_TIME,
        "total_damage": TOTAL_DAMAGE,
        "dps": DPS,
        "total_reward": total_reward,
        "reward_formula": REWARD_FORMULA,
        "remaining_return_definition": "undiscounted inclusive reverse cumulative immediate reward",
        "action_data_hash": action_hash,
        "party_config_hash": party_hash,
        "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
        "no_character_specific_usage_reward_bonus": True,
        "reward_shaping": False,
        "future_information_used_as_policy_input": False,
        "training_only": True,
        "global_optimum_claimed": False,
        "human_authored_route": True,
        "action_distribution": dict(Counter(action_ids)),
        "resolved_action_distribution": dict(Counter(resolved_action_ids)),
        "active_character_distribution": dict(Counter(active_characters)),
    }

    rewards_array = np.asarray(rewards, dtype=np.float64)
    damages_array = np.asarray(damages, dtype=np.float64)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        observations=np.asarray(observations, dtype=np.float32),
        action_indices=np.asarray(action_indices, dtype=np.int64),
        action_ids=np.asarray(action_ids, dtype=str),
        action_masks=np.asarray(action_masks, dtype=bool),
        resolved_action_ids=np.asarray(resolved_action_ids, dtype=str),
        active_characters=np.asarray(active_characters, dtype=str),
        rewards=rewards_array,
        damages=damages_array,
        combat_time_costs=np.asarray(combat_time_costs, dtype=np.float64),
        combat_times_before=np.asarray(combat_times_before, dtype=np.float64),
        combat_times_after=np.asarray(combat_times_after, dtype=np.float64),
        action_times_before=np.asarray(action_times_before, dtype=np.float64),
        action_times_after=np.asarray(action_times_after, dtype=np.float64),
        episode_ids=np.asarray([EPISODE_ID] * SAMPLE_COUNT, dtype=str),
        step_indices=np.arange(SAMPLE_COUNT, dtype=np.int64),
        terminated=np.asarray(terminated_values, dtype=bool),
        truncated=np.asarray(truncated_values, dtype=bool),
        remaining_returns=reverse_cumulative(rewards_array),
        remaining_damage=reverse_cumulative(damages_array),
        observation_versions=np.asarray([OBSERVATION_VERSION] * SAMPLE_COUNT, dtype=str),
        action_data_hashes=np.asarray([action_hash] * SAMPLE_COUNT, dtype=str),
        party_config_hashes=np.asarray([party_hash] * SAMPLE_COUNT, dtype=str),
        route_ids=np.asarray([ROUTE_ID] * SAMPLE_COUNT, dtype=str),
        metadata_json=np.asarray(json.dumps(metadata, ensure_ascii=False, sort_keys=True), dtype=str),
    )
    return metadata


def build_summary(output_path: Path, *, small_overfit_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    demo = load_demo_npz(output_path)
    env = _make_env()
    env.reset(seed=0)
    contract_validation = validate_demo_contract(demo, env, root=ROOT)
    replay_validation = replay_validate_demo(demo, _make_env)
    alias_validation = alias_audit(demo)
    legacy_rejections = [
        validate_legacy_demo_rejected(path)
        for path in LEGACY_DEMO_PATHS
        if path.exists()
    ]
    metadata = demo["metadata"]
    summary = {
        "schema_version": "manual_120s_bc_demonstration_summary_v1",
        "candidate_label": CANDIDATE_LABEL,
        "candidate_status": "implemented_tests_passed_pending_external_review",
        "dataset_path": project_relative_posix(output_path, root=ROOT),
        "dataset_sha256": file_sha256(output_path),
        "array_manifest": array_manifest(demo),
        "required_arrays": list(REQUIRED_ARRAYS),
        "metadata": metadata,
        "episode_count": 1,
        "sample_count": SAMPLE_COUNT,
        "observation_contract": {
            "observation_version": OBSERVATION_VERSION,
            "observation_shape": list(OBSERVATION_SHAPE),
            "future_information_used_as_policy_input": False,
        },
        "action_contract": {
            "policy_action_count": POLICY_ACTION_COUNT,
            "max_policy_action_slots": MAX_POLICY_ACTION_SLOTS,
            "policy_action_ids": metadata["policy_action_ids"],
        },
        "hashes": {
            "action_data_hash": metadata["action_data_hash"],
            "party_config_hash": metadata["party_config_hash"],
            "direct_action_manifest_sha256": DIRECT_ACTION_MANIFEST_SHA256,
            "source_route_file_sha256": metadata["source_route_file_sha256"],
            "selected_sequence_sha256": SELECTED_SEQUENCE_SHA256,
            "resolved_sequence_sha256": RESOLVED_SEQUENCE_SHA256,
        },
        "runtime_totals": {
            "final_combat_time": FINAL_COMBAT_TIME,
            "total_damage": TOTAL_DAMAGE,
            "dps": DPS,
            "total_reward": metadata["total_reward"],
        },
        "distributions": {
            "action_distribution": distribution(demo["action_ids"]),
            "resolved_action_distribution": distribution(demo["resolved_action_ids"]),
            "active_character_distribution": distribution(demo["active_characters"]),
        },
        "contract_validation": contract_validation,
        "replay_validation": replay_validation,
        "alias_audit": alias_validation,
        "legacy_dataset_rejections": legacy_rejections,
        "bc_small_overfit_smoke_metrics": small_overfit_metrics or {"status": "not_run_yet"},
        "full_training_executed": False,
        "post_review_commands": [
            (
                ".\\.venv\\Scripts\\python.exe rl\\pretrain_maskable_ppo_bc.py `\n"
                "  --party aemeath_mornye_lynae_enabled_test_party `\n"
                "  --initial-active-character aemeath `\n"
                "  --demo-path data\\generated\\manual_120s_bc_demonstration_v105.npz `\n"
                "  --model-path models\\maskable_ppo_bc_v105.zip `\n"
                "  --epochs 300 `\n"
                "  --batch-size 148 `\n"
                "  --learning-rate 0.003 `\n"
                "  --seed 11 `\n"
                "  --device cpu"
            ),
            (
                ".\\.venv\\Scripts\\python.exe rl\\evaluate_maskable_ppo.py `\n"
                "  --model-path models\\maskable_ppo_bc_v105.zip `\n"
                "  --party aemeath_mornye_lynae_enabled_test_party `\n"
                "  --initial-active-character aemeath"
            ),
            (
                ".\\.venv\\Scripts\\python.exe rl\\train_maskable_ppo.py `\n"
                "  --party aemeath_mornye_lynae_enabled_test_party `\n"
                "  --initial-active-character aemeath `\n"
                "  --curriculum-reset-mode none `\n"
                "  --load-model models\\maskable_ppo_bc_v105.zip `\n"
                "  --model-path models\\maskable_ppo_candidate_after_bc_v105.zip `\n"
                "  --timesteps 100000 `\n"
                "  --seed 42"
            ),
        ],
        "explicit_non_actions": [
            "No full BC training was executed by this candidate generation step.",
            "No long PPO training was executed.",
            "No simulator combat mechanics, reward formula, action data, action order, observation schema, build profiles, or 120-second route were changed.",
        ],
    }
    return summary


def write_summary_and_report(
    output_path: Path = DEFAULT_DEMO_PATH,
    *,
    summary_path: Path = SUMMARY_PATH,
    report_path: Path = REPORT_PATH,
    small_overfit_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = build_summary(output_path, small_overfit_metrics=small_overfit_metrics)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _write_text(summary_path, json.dumps(summary, indent=2, ensure_ascii=False))
    _write_text(report_path, _render_report(summary))
    return summary


def _render_report(summary: dict[str, Any]) -> str:
    arrays = summary["array_manifest"]
    lines = [
        "# Manual 120s BC Demonstration Candidate 106",
        "",
        "- Candidate status: pending external review",
        "- Source verified baseline: 105",
        f"- Dataset: `{summary['dataset_path']}`",
        f"- Dataset SHA-256: `{summary['dataset_sha256']}`",
        f"- Samples: {summary['sample_count']} across {summary['episode_count']} episode",
        f"- Observation: {summary['observation_contract']['observation_version']} / {summary['observation_contract']['observation_shape']}",
        f"- Policy actions: {summary['action_contract']['policy_action_count']} (max slots {summary['action_contract']['max_policy_action_slots']})",
        f"- Selected hash: `{summary['hashes']['selected_sequence_sha256']}`",
        f"- Resolved hash: `{summary['hashes']['resolved_sequence_sha256']}`",
        f"- Final combat time: {summary['runtime_totals']['final_combat_time']}",
        f"- Total damage: {summary['runtime_totals']['total_damage']}",
        f"- DPS: {summary['runtime_totals']['dps']}",
        f"- Total reward: {summary['runtime_totals']['total_reward']}",
        f"- Action data hash: `{summary['hashes']['action_data_hash']}`",
        f"- Party config hash: `{summary['hashes']['party_config_hash']}`",
        f"- Direct action manifest SHA-256: `{summary['hashes']['direct_action_manifest_sha256']}`",
        "",
        "## Arrays",
        "",
    ]
    for name in summary["required_arrays"]:
        manifest = arrays[name]
        lines.append(f"- `{name}`: dtype `{manifest['dtype']}`, shape `{manifest['shape']}`")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Contract validation: {summary['contract_validation']['status']}",
            f"- Replay validation: {summary['replay_validation']['status']}",
            (
                f"- Alias audit: {summary['alias_audit']['unique_observation_mask_keys']} unique observation+mask keys, "
                f"{summary['alias_audit']['conflicting_target_key_count']} conflicts"
            ),
            f"- Legacy stale demos rejected: {len(summary['legacy_dataset_rejections'])}",
            "",
            "## BC Small-Overfit Smoke",
            "",
            f"- Status: {summary['bc_small_overfit_smoke_metrics'].get('status')}",
        ]
    )
    metrics = summary["bc_small_overfit_smoke_metrics"]
    for key in ("initial_masked_nll", "final_masked_nll", "nll_decrease", "final_top1_accuracy", "invalid_top1_count"):
        if key in metrics:
            lines.append(f"- {key}: {metrics[key]}")
    lines.extend(
        [
            "",
            "## Training Boundary",
            "",
            "- Full BC training was not executed.",
            "- Long PPO training was not executed.",
            "- Remaining return, remaining damage, step index, route ID, episode ID, and resolved action ID are diagnostics only and are not part of the 314-dimensional observation.",
            "",
            "## Post-Review Commands",
            "",
        ]
    )
    for command in summary["post_review_commands"]:
        lines.extend(["```powershell", command, "```", ""])
    return "\n".join(lines) + "\n"


def _write_text(path: Path, text: str) -> None:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_bytes(normalized.encode("utf-8"))


def _make_env() -> WuwaDpsEnv:
    return WuwaDpsEnv(
        ROOT / "data",
        party=PARTY_ID,
        initial_active_character=INITIAL_ACTIVE_CHARACTER,
        curriculum_reset_mode=CURRICULUM_RESET_MODE,
    )


def _invalid_action_message(
    env: WuwaDpsEnv,
    index: int,
    action_id: str,
    policy_action_ids: list[str],
    mask: np.ndarray,
) -> str:
    valid = [policy_action_ids[i] for i, allowed in enumerate(mask) if bool(allowed)]
    return json.dumps(
        {
            "error": "manual 120s BC route selected an invalid action",
            "row": index,
            "step": index + 1,
            "action_id": action_id,
            "active_character": env.simulation.state.active_character_id,
            "valid_policy_actions": valid,
            "combat_time": env.simulation.state.combat_time,
            "action_time": env.simulation.state.current_time,
            "cooldowns": env.simulation.state.cooldowns,
            "resonance_energy": env.simulation.state.resonance_energy,
            "concerto_energy": env.simulation.state.concerto_energy,
        },
        indent=2,
        default=str,
    )


def main() -> None:
    args = build_arg_parser().parse_args()
    metadata = generate_manual_120s_bc_demonstration(args.output)
    summary = write_summary_and_report(args.output, summary_path=args.summary_path, report_path=args.report_path)
    print(
        json.dumps(
            {
                "status": "ok",
                "dataset_path": project_relative_posix(args.output, root=ROOT),
                "dataset_sha256": summary["dataset_sha256"],
                "sample_count": metadata["sample_count"],
                "selected_sequence_sha256": metadata["selected_sequence_sha256"],
                "resolved_sequence_sha256": metadata["resolved_sequence_sha256"],
                "total_damage": metadata["total_damage"],
                "dps": metadata["dps"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
