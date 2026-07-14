from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.wuwa_env import WuwaDpsEnv
from rl.demo_contract import (
    OBSERVATION_SHAPE,
    OBSERVATION_VERSION,
    action_data_hash,
    party_config_hash,
    sequence_hash,
)
from simulator.simulation import Simulation


PARTY = "aemeath_mornye_lynae_enabled_test_party"
INITIAL_ACTIVE = "aemeath"
ROUTE_PATH = Path("data/manual_120s_baseline_routes_v104.json")
OLD_SUMMARY_PATH = Path("results/manual_120s_baseline_v104_summary.json")
MANUAL_SUMMARY_PATH = Path("results/manual_120s_baseline_v114_summary.json")
MANUAL_TIMELINE_PATH = Path("results/manual_120s_baseline_v114_timeline.csv")
MANUAL_REPORT_PATH = Path("reports/manual_120s_baseline_v114.md")
REEVAL_ROOT = Path("results/transition_contract_v114_model_reevaluation")
LEADERBOARD_PATH = REEVAL_ROOT / "leaderboard.json"
REEVAL_REPORT_PATH = Path("reports/transition_contract_v114_model_reevaluation.md")
COMPARISON_PATH = Path("results/manual_model_comparison_v114.json")
OUTRO_BUFF_ID = "aemeath_outro_unseen_guard_all_damage_amp"
EXPECTED_ROUTE_SHA = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temp, path)


def runtime_contract() -> dict[str, Any]:
    sim = Simulation.from_json(ROOT / "data", party=PARTY, initial_active_character=INITIAL_ACTIVE)
    order = sim.get_policy_action_ids()
    return {
        "transition_contract_version": "v114",
        "party": PARTY,
        "initial_active_character": INITIAL_ACTIVE,
        "observation_version": OBSERVATION_VERSION,
        "observation_shape": int(OBSERVATION_SHAPE[0]),
        "policy_action_count": len(order),
        "policy_action_order": order,
        "policy_action_order_sha256": sequence_hash(order),
        "action_data_hash": action_data_hash(root=ROOT),
        "party_config_hash": party_config_hash(root=ROOT),
        "transition_config_sha256": sha256(ROOT / "data/transition_config.json"),
        "buffs_sha256": sha256(ROOT / "data/buffs.json"),
        "manual_route_raw_sha256": sha256(ROOT / ROUTE_PATH),
        "generic_swap_source_status": "user_approved_benchmark_assumption_after_workbook_and_web_review",
        "aemeath_outro_implementation_version": "implemented_v114",
    }


def outro_values(sim: Simulation) -> dict[str, tuple[float, float]]:
    return {
        active.target_character_id: (
            float(active.metadata.get("dynamic_value", 0.1) or 0.0),
            float(active.remaining_duration),
        )
        for active in sim.state.active_buffs
        if active.buff_id == OUTRO_BUFF_ID and active.target_character_id and active.remaining_duration > 0.0
    }


def is_aemeath_outro_base_cast(row: Any) -> bool:
    return bool(
        row.aemeath_outro_applied
        and row.outgoing_character_id == "aemeath"
        and row.outgoing_outro_event_id == "aemeath_outro_unseen_guard"
    )


def replay_manual() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = json.loads((ROOT / ROUTE_PATH).read_text(encoding="utf-8"))
    route = list(raw["routes"]["primary"]["selected_policy_actions"])
    sim = Simulation.from_json(ROOT / "data", party=PARTY, initial_active_character=INITIAL_ACTIVE)
    selected: list[str] = []
    resolved: list[str] = []
    invalid: list[dict[str, Any]] = []
    blocked_swaps = 0
    uptime = defaultdict(lambda: {"base_0_10_seconds": 0.0, "enhanced_0_20_seconds": 0.0})
    outro_damage_gain = 0.0

    def execute(action_id: str, *, padding: bool = False) -> bool:
        nonlocal blocked_swaps, outro_damage_gain
        before = outro_values(sim)
        prior_timeline = len(sim.timeline)
        ok = sim.execute_action(action_id)
        selected.append(action_id)
        if not ok:
            target = action_id.removeprefix("swap_to_") if action_id.startswith("swap_to_") else None
            blocked = bool(target and sim.state.cooldowns.get(f"swap_reentry:{target}", 0.0) > 0.0)
            blocked_swaps += int(blocked)
            invalid.append(
                {
                    "selected_index": len(selected) - 1,
                    "action_id": action_id,
                    "combat_time": sim.state.combat_time,
                    "active_character_id": sim.state.active_character_id,
                    "swap_reentry_blocked": blocked,
                    "padding": padding,
                }
            )
            return False
        assert len(sim.timeline) == prior_timeline + 1
        row = sim.timeline[-1]
        resolved.append(row.resolved_action_id or row.action_id)
        elapsed = float(row.effective_combat_time_cost)
        applied_during_transition = bool(row.aemeath_outro_applied and row.outgoing_character_id == "aemeath")
        for character_id in ("mornye", "lynae"):
            value_remaining = before.get(character_id)
            if value_remaining is None and applied_during_transition:
                value_remaining = (0.1, 20.0)
            if value_remaining is None:
                continue
            amp, remaining = value_remaining
            active_seconds = min(elapsed, remaining)
            key = "enhanced_0_20_seconds" if amp >= 0.2 - 1e-9 else "base_0_10_seconds"
            uptime[character_id][key] += active_seconds
        actor = row.actor_character_id
        action_amp = before.get(actor, (0.0, 0.0))[0] if actor else 0.0
        if applied_during_transition and actor and actor != "aemeath":
            action_amp = 0.1
        if action_amp > 0.0:
            for detail in row.hit_details:
                if OUTRO_BUFF_ID not in detail.get("applied_buff_summary", []):
                    continue
                total_amp = float(detail.get("applied_damage_amp", 0.0) or 0.0)
                damage = float(detail.get("damage", 0.0) or 0.0)
                outro_damage_gain += damage * action_amp / max(1e-12, 1.0 + total_amp)
        return True

    for action_id in route:
        if sim.state.combat_time >= sim.combat_duration:
            break
        execute(action_id)

    # The immutable v104 route lost its placeholder swap seconds under v114.
    # Deterministic policy-visible waits complete the 120s evaluation without
    # changing the raw route bytes.
    padding_actions = 0
    while sim.state.combat_time < sim.combat_duration and padding_actions < 5000:
        if not execute("short_wait", padding=True):
            break
        padding_actions += 1

    timeline = [row.model_dump(mode="json") for row in sim.timeline]
    generic_swaps = [row for row in sim.timeline if row.generic_swap_zero_time]
    outro_rows = [row for row in sim.timeline if is_aemeath_outro_base_cast(row)]
    upgrade_rows = [row for row in sim.timeline if row.aemeath_outro_upgraded_character_ids]
    old = json.loads((ROOT / OLD_SUMMARY_PATH).read_text(encoding="utf-8"))
    contract = runtime_contract()
    summary = {
        "schema_version": "manual_120s_baseline_v114",
        "candidate": 114,
        "external_review_status": "pending",
        "runtime_contract": contract,
        "raw_route_path": ROUTE_PATH.as_posix(),
        "raw_route_sha256": contract["manual_route_raw_sha256"],
        "raw_route_action_count": len(route),
        "padding_action_count": padding_actions,
        "route_valid": not invalid,
        "invalid_action_count": len(invalid),
        "invalid_actions": invalid,
        "selected_action_count": len(selected),
        "executed_action_count": len(resolved),
        "selected_action_sequence": selected,
        "resolved_action_sequence": resolved,
        "selected_route_sha256": sequence_hash(selected),
        "resolved_route_sha256": sequence_hash(resolved),
        "total_damage": float(sim.state.total_damage),
        "dps": float(sim.state.total_damage / 120.0),
        "final_combat_time": float(sim.state.combat_time),
        "final_current_time": float(sim.state.current_time),
        "completed_120s": sim.state.combat_time >= 120.0 - 1e-9,
        "truncated_at_120s": bool(sim.timeline and sim.timeline[-1].truncated_by_combat_limit),
        "generic_swap_count": len(generic_swaps),
        "removed_placeholder_swap_time_seconds": 0.5 * len(generic_swaps),
        "swap_reentry_blocked_count": blocked_swaps,
        "aemeath_outro_cast_count": len(outro_rows),
        "aemeath_outro_upgrade_count": sum(len(row.aemeath_outro_upgraded_character_ids) for row in upgrade_rows),
        "aemeath_outro_upgrade_counts_by_recipient": dict(
            Counter(character for row in upgrade_rows for character in row.aemeath_outro_upgraded_character_ids)
        ),
        "aemeath_outro_uptime_by_recipient": dict(uptime),
        "aemeath_outro_direct_hit_damage_gain": outro_damage_gain,
        "final_aemeath_outro_recipient_state": {
            character_id: {"value": amp, "remaining_duration": remaining}
            for character_id, (amp, remaining) in outro_values(sim).items()
        },
        "action_counts": dict(Counter(selected)),
        "comparison_to_v104": {
            "v104_total_damage": float(old["total_damage"]),
            "v104_dps": float(old["dps"]),
            "v104_final_combat_time": float(old["final_combat_time"]),
            "v104_final_current_time": float(old["final_current_time"]),
            "total_damage_delta": float(sim.state.total_damage - float(old["total_damage"])),
            "dps_delta": float(sim.state.total_damage / 120.0 - float(old["dps"])),
            "current_time_delta": float(sim.state.current_time - float(old["final_current_time"])),
            "executed_action_count_delta": len(resolved) - len(old.get("resolved_action_sequence", [])),
        },
        "canonical_bc_npz_status": (
            "immutable_historical_training_data; v114 transition contract requires a future regenerated "
            "demonstration before retraining"
        ),
        "training_executed": False,
    }
    return summary, timeline


def write_manual(summary: dict[str, Any], timeline: list[dict[str, Any]]) -> None:
    write_json(ROOT / MANUAL_SUMMARY_PATH, summary)
    fields = [
        "index", "selected_action_id", "resolved_action_id", "actor_character_id", "active_character_before",
        "active_character_after", "time_start", "time_end", "combat_time_start", "combat_time_end",
        "action_time", "effective_combat_time_cost", "damage", "generic_swap_zero_time",
        "outgoing_swap_reentry_key", "outgoing_swap_reentry_after_action", "aemeath_outro_applied",
        "aemeath_outro_upgrade_applied",
        "aemeath_outro_mode_snapshot", "aemeath_outro_recipient_values_after",
        "aemeath_outro_upgraded_character_ids", "aemeath_outro_upgrade_event_tag",
    ]
    path = ROOT / MANUAL_TIMELINE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(timeline):
            payload = {key: row.get(key) for key in fields}
            payload["index"] = index
            for key in ("aemeath_outro_recipient_values_after", "aemeath_outro_upgraded_character_ids"):
                payload[key] = json.dumps(payload[key], ensure_ascii=False, sort_keys=True)
            writer.writerow(payload)
    os.replace(temp, path)
    comparison = summary["comparison_to_v104"]
    lines = [
        "# Manual 120s baseline v114",
        "",
        "Candidate 114 is pending external review. This deterministic replay uses the immutable v104 raw route, then policy-visible short waits to reach 120 combat seconds after removal of placeholder swap time.",
        "",
        f"- Total damage / DPS: `{summary['total_damage']}` / `{summary['dps']}`",
        f"- Combat/current time: `{summary['final_combat_time']}` / `{summary['final_current_time']}`",
        f"- Delta from v104: damage `{comparison['total_damage_delta']}`, DPS `{comparison['dps_delta']}`",
        f"- Generic swaps / removed placeholder time: `{summary['generic_swap_count']}` / `{summary['removed_placeholder_swap_time_seconds']}s`",
        f"- Re-entry blocks: `{summary['swap_reentry_blocked_count']}`",
        f"- Aemeath Outro casts/upgrades: `{summary['aemeath_outro_cast_count']}` / `{summary['aemeath_outro_upgrade_count']}`",
        f"- Aemeath Outro direct-hit damage gain: `{summary['aemeath_outro_direct_hit_damage_gain']}`",
        f"- Route valid / invalid actions: `{summary['route_valid']}` / `{summary['invalid_action_count']}`",
        f"- Raw/executed/padding action counts: `{summary['raw_route_action_count']}` / `{summary['executed_action_count']}` / `{summary['padding_action_count']}`",
        "",
        "## Recipient uptime",
        "",
    ]
    for recipient, metrics in summary["aemeath_outro_uptime_by_recipient"].items():
        lines.append(
            f"- {recipient}: base 10% `{metrics['base_0_10_seconds']}s`; enhanced 20% `{metrics['enhanced_0_20_seconds']}s`"
        )
    write_text(ROOT / MANUAL_REPORT_PATH, "\n".join(lines))


def model_paths() -> list[Path]:
    paths = [
        ROOT / "models/maskable_ppo_bc_v105.zip",
        ROOT / "models/maskable_ppo_candidate_after_bc_v105.zip",
    ]
    paths.extend(sorted((ROOT / "models/guarded_ppo_v109").rglob("*.zip")))
    return paths


def sidecar_for(model_path: Path) -> Path | None:
    for suffix in (".bc_metadata.json", ".ppo_metadata.json"):
        candidate = Path(str(model_path) + suffix)
        if candidate.exists():
            return candidate
    return None


def evaluate_model(model_path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    from sb3_contrib import MaskablePPO

    np.random.seed(114)
    torch.manual_seed(114)
    torch.set_num_threads(1)
    model = MaskablePPO.load(model_path, device="cpu")
    env = WuwaDpsEnv(
        ROOT / "data",
        party=PARTY,
        initial_active_character=INITIAL_ACTIVE,
        curriculum_reset_mode="none",
    )
    observation, _ = env.reset(seed=114)
    order = env.simulation.get_policy_action_ids()
    model_observation_shape = list(model.observation_space.shape)
    model_action_count = int(model.action_space.n)
    assert model_observation_shape == [314], (model_path, model_observation_shape)
    assert model_action_count == 25, (model_path, model_action_count)
    selected: list[str] = []
    resolved: list[str] = []
    invalid = 0
    reentry_blocks = 0
    step_count = 0
    while env.simulation.state.combat_time < 120.0 and step_count < 10000:
        mask = env.action_masks()
        assert mask.shape == (25,)
        action, _ = model.predict(observation, deterministic=True, action_masks=mask)
        action_id = order[int(action)]
        before_cooldown = float(
            env.simulation.state.cooldowns.get(f"swap_reentry:{action_id.removeprefix('swap_to_')}", 0.0)
            if action_id.startswith("swap_to_")
            else 0.0
        )
        observation, _reward, terminated, truncated, info = env.step(int(action))
        selected.append(action_id)
        resolved.append(str(info.get("resolved_action_id")))
        invalid += int(bool(info.get("invalid_action", False)))
        reentry_blocks += int(bool(info.get("invalid_action", False)) and before_cooldown > 0.0)
        step_count += 1
        if terminated or truncated:
            break
    sidecar_path = sidecar_for(model_path)
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8")) if sidecar_path else {}
    timeline = env.simulation.timeline
    return {
        "schema_version": "transition_contract_v114_model_evaluation",
        "candidate": 114,
        "model_path": model_path.relative_to(ROOT).as_posix(),
        "model_sha256": sha256(model_path),
        "source_sidecar_path": sidecar_path.relative_to(ROOT).as_posix() if sidecar_path else None,
        "source_sidecar_sha256": sha256(sidecar_path) if sidecar_path else None,
        "source_sidecar_contract": {
            key: sidecar.get(key)
            for key in (
                "observation_version", "observation_shape", "policy_action_count", "policy_action_order",
                "selected_party_character_ids", "initial_active_character", "curriculum_reset_mode",
                "action_data_hash", "party_config_hash",
            )
        },
        "v114_runtime_contract": contract,
        "documented_allowed_contract_drift": [
            "generic swap placeholder timing replaced by v114 zero-time/re-entry contract",
            "Aemeath Outro transition/buff contract added",
            "party/transition/buff hashes may differ from training sidecar",
        ],
        "model_loadable": True,
        "model_observation_shape": model_observation_shape,
        "model_action_count": model_action_count,
        "action_mask_width": 25,
        "deterministic": True,
        "total_damage": float(env.simulation.state.total_damage),
        "dps": float(env.simulation.state.total_damage / 120.0),
        "final_combat_time": float(env.simulation.state.combat_time),
        "final_current_time": float(env.simulation.state.current_time),
        "completed_120s": env.simulation.state.combat_time >= 120.0 - 1e-9,
        "truncated_at_120s": bool(timeline and timeline[-1].truncated_by_combat_limit),
        "step_count": step_count,
        "invalid_action_count": invalid,
        "swap_reentry_blocked_count": reentry_blocks,
        "aemeath_outro_cast_count": sum(int(is_aemeath_outro_base_cast(row)) for row in timeline),
        "aemeath_outro_upgrade_count": sum(len(row.aemeath_outro_upgraded_character_ids) for row in timeline),
        "selected_route_sha256": sequence_hash(selected),
        "resolved_route_sha256": sequence_hash(resolved),
        "selected_action_sequence": selected,
        "resolved_action_sequence": resolved,
    }


def evaluate_models(contract: dict[str, Any]) -> dict[str, Any]:
    evaluations = []
    for path in model_paths():
        result = evaluate_model(path, contract)
        evaluations.append(result)
        output = ROOT / REEVAL_ROOT / "evaluations" / (path.relative_to(ROOT / "models").as_posix().replace("/", "__") + ".json")
        write_json(output, result)
    ranked = sorted(
        evaluations,
        key=lambda item: (bool(item["completed_120s"]), float(item["total_damage"]), item["model_path"]),
        reverse=True,
    )
    leaderboard = {
        "schema_version": "transition_contract_v114_model_reevaluation_leaderboard",
        "candidate": 114,
        "external_review_status": "pending",
        "winner_selection": "maximum deterministic completed 120-second total damage",
        "runtime_contract": contract,
        "evaluation_count": len(ranked),
        "winner": ranked[0],
        "rankings": [
            {
                "rank": index + 1,
                **{
                    key: row[key]
                    for key in (
                        "model_path", "model_sha256", "total_damage", "dps", "completed_120s",
                        "final_combat_time", "invalid_action_count", "swap_reentry_blocked_count",
                        "aemeath_outro_cast_count", "aemeath_outro_upgrade_count", "selected_route_sha256",
                        "resolved_route_sha256",
                    )
                },
            }
            for index, row in enumerate(ranked)
        ],
        "training_executed": False,
    }
    write_json(ROOT / LEADERBOARD_PATH, leaderboard)
    return leaderboard


def write_model_report(leaderboard: dict[str, Any]) -> None:
    lines = [
        "# Transition contract v114 model re-evaluation",
        "",
        "Candidate 114 is pending external review. All entries are deterministic inference-only 120-second evaluations; no model or sidecar was altered.",
        "",
        f"Winner: `{leaderboard['winner']['model_path']}` with `{leaderboard['winner']['total_damage']}` damage (`{leaderboard['winner']['dps']}` DPS).",
        "",
        "| Rank | Model | Damage | DPS | Completed | Invalid | Re-entry blocks | Outro casts/upgrades |",
        "|---:|---|---:|---:|:---:|---:|---:|---:|",
    ]
    for row in leaderboard["rankings"]:
        lines.append(
            f"| {row['rank']} | `{row['model_path']}` | {row['total_damage']} | {row['dps']} | "
            f"{row['completed_120s']} | {row['invalid_action_count']} | {row['swap_reentry_blocked_count']} | "
            f"{row['aemeath_outro_cast_count']}/{row['aemeath_outro_upgrade_count']} |"
        )
    write_text(ROOT / REEVAL_REPORT_PATH, "\n".join(lines))


def build_comparison(manual: dict[str, Any], leaderboard: dict[str, Any]) -> dict[str, Any]:
    rankings = leaderboard["rankings"]
    entries = [
        {
            "kind": "manual_v114",
            "result_path": MANUAL_SUMMARY_PATH.as_posix(),
            "total_damage": manual["total_damage"],
            "dps": manual["dps"],
            "completed_120s": manual["completed_120s"],
            "model_path": None,
        }
    ]
    entries.extend({"kind": "existing_model_v114", "result_path": LEADERBOARD_PATH.as_posix(), **row} for row in rankings)
    completed = [entry for entry in entries if entry["completed_120s"]]
    winner = max(completed, key=lambda entry: (float(entry["total_damage"]), str(entry.get("model_path") or "manual")))
    return {
        "schema_version": "manual_model_comparison_v114",
        "candidate": 114,
        "objective": "maximum deterministic completed 120-second total damage",
        "entries": entries,
        "current_best": winner,
        "canonical_bc_npz_status": (
            "immutable historical training data; stale for future retraining under the v114 transition contract"
        ),
        "training_executed": False,
    }


def dry_run_plan(project_root: Path) -> dict[str, Any]:
    global ROOT
    ROOT = project_root.resolve()
    contract = runtime_contract()
    assert contract["manual_route_raw_sha256"] == EXPECTED_ROUTE_SHA
    assert contract["observation_version"] == "slot_generic_mechanics_v5"
    assert contract["observation_shape"] == 314
    assert contract["policy_action_count"] == 25
    return {
        "schema_version": "transition_contract_v114_rebaseline_plan",
        "mode": "dry_run",
        "project_root": str(ROOT),
        "runtime_contract": contract,
        "manual_outputs": [MANUAL_SUMMARY_PATH.as_posix(), MANUAL_TIMELINE_PATH.as_posix(), MANUAL_REPORT_PATH.as_posix()],
        "model_count": len(model_paths()),
        "model_output_root": REEVAL_ROOT.as_posix(),
        "comparison_output": COMPARISON_PATH.as_posix(),
        "training_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--evaluate-all-existing-checkpoints", action="store_true")
    args = parser.parse_args(argv)
    plan = dry_run_plan(args.project_root)
    if not args.execute:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0
    if not args.evaluate_all_existing_checkpoints:
        raise SystemExit("--execute requires --evaluate-all-existing-checkpoints for the complete v114 contract")
    manual, timeline = replay_manual()
    write_manual(manual, timeline)
    leaderboard = evaluate_models(plan["runtime_contract"])
    write_model_report(leaderboard)
    comparison = build_comparison(manual, leaderboard)
    write_json(ROOT / COMPARISON_PATH, comparison)
    print(
        json.dumps(
            {
                "manual_total_damage": manual["total_damage"],
                "manual_dps": manual["dps"],
                "model_evaluation_count": leaderboard["evaluation_count"],
                "model_winner": leaderboard["winner"]["model_path"],
                "model_winner_total_damage": leaderboard["winner"]["total_damage"],
                "current_best": comparison["current_best"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
