from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import (
    ACCOUNT_OBSERVATION_SHAPE,
    ACCOUNT_OBSERVATION_VERSION,
    build_account_observation_labels,
)
from scripts.v124_timing_test_support import make_sim


JSON_REPORT = ROOT / "reports" / "timing_markov_state_observation_audit_v124.json"
MD_REPORT = ROOT / "reports" / "timing_markov_state_observation_audit_v124.md"
EXPECTED_LABEL_HASH = "b32bfb6fc3287ccf10bef65b9ac146902c69cb0b1ce6808ef0acadf7bc50e374"
EXPECTED_INITIAL_VECTOR_HASH = "6ccc4a5f228329c7b02ed72d4b1354cffc0c8a222d0ed1115be40316a18b3a4f"


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def finding(
    item: str,
    *,
    present: bool,
    derivable: bool,
    risk: str,
    recommendation: str,
    note: str,
) -> dict:
    return {
        "item": item,
        "future_transition_reward_affected": True,
        "present_in_v6_observation": present,
        "derivable_from_current_observation_and_action_history": derivable,
        "markov_aliasing_risk": risk,
        "recommended_v7_field_or_aggregation": recommendation,
        "finding": note,
    }


def build_report() -> dict:
    labels = build_account_observation_labels()
    initial_values = make_sim("mornye").account_observation_values()
    labels_hash = canonical_hash(labels)
    vector_hash = canonical_hash(initial_values)
    if labels_hash != EXPECTED_LABEL_HASH or vector_hash != EXPECTED_INITIAL_VECTOR_HASH:
        raise AssertionError("account observation v6/330 changed during timing-core-1")
    findings = [
        finding("ongoing action owner", present=False, derivable=False, risk="high", recommendation="ongoing_action_owner_slot", note="Different off-field owners change persistence, cancellation, and future packet ownership."),
        finding("ongoing action source ID or behavior class", present=False, derivable=False, risk="high", recommendation="ongoing_action_behavior_class", note="Actions with identical visible resources can have different remaining locks, tails, and packet rules."),
        finding("time until same-character input unlock", present=False, derivable=False, risk="high", recommendation="same_input_lock_remaining", note="The action-slot available bit does not expose the unlock horizon."),
        finding("time until swap unlock", present=False, derivable=False, risk="high", recommendation="swap_lock_remaining", note="The action-slot available bit aliases 1F and long swap-lock states."),
        finding("time until action end", present=False, derivable=False, risk="high", recommendation="action_end_remaining", note="Control may return while the source action and reward tail remain active."),
        finding("character persistence after swap", present=False, derivable=False, risk="high", recommendation="persistent_off_field_owner_slot", note="Persistent execution changes cancellation and future packet outcomes."),
        finding("time until persistence cutoff", present=False, derivable=False, risk="high", recommendation="persistence_cutoff_remaining", note="The same visible swap can select different persistence branches."),
        finding("pending packet count", present=False, derivable=False, risk="high", recommendation="pending_packet_count", note="Pending reward multiplicity is not represented by scheduled-effect v5 channels."),
        finding("time until next packet", present=False, derivable=False, risk="high", recommendation="next_packet_time_remaining", note="Near and distant packet states alias under v6."),
        finding("time until final packet", present=False, derivable=False, risk="high", recommendation="last_packet_time_remaining", note="Tail completion changes future reward and action-instance lifetime."),
        finding("pending packet behavior class", present=False, derivable=False, risk="high", recommendation="pending_packet_behavior_class", note="Detachable, cancellable, and persistent packet families are behaviorally distinct."),
        finding("pending damage/resource/marker/buff flags", present=False, derivable=False, risk="high", recommendation="pending_packet_effect_flags", note="Equal packet counts can affect different transition and reward channels."),
        finding("character re-entry cooldowns", present=True, derivable=True, risk="low", recommendation="character_reentry_remaining_by_slot", note="Fixed policy action slots currently expose target swap cooldown ratios and availability, but a slot-generic v7 aggregation is clearer."),
    ]
    hidden_not_derivable = [row["item"] for row in findings if not row["present_in_v6_observation"] and not row["derivable_from_current_observation_and_action_history"]]
    return {
        "schema_version": "timing_markov_state_observation_audit_v124",
        "candidate": 124,
        "stage": "timing-core-1",
        "observation_version": ACCOUNT_OBSERVATION_VERSION,
        "observation_v6_shape": ACCOUNT_OBSERVATION_SHAPE,
        "observation_v6_modified": False,
        "observation_v6_labels_sha256_before": EXPECTED_LABEL_HASH,
        "observation_v6_labels_sha256_after": labels_hash,
        "observation_v6_initial_vector_sha256_before": EXPECTED_INITIAL_VECTOR_HASH,
        "observation_v6_initial_vector_sha256_after": vector_hash,
        "findings": findings,
        "hidden_future_affecting_state_not_derivable": hidden_not_derivable,
        "markov_aliasing_found": bool(hidden_not_derivable),
        "observation_v7_required": bool(hidden_not_derivable),
        "recommended_compact_v7_fields": [
            "ongoing_action_owner_slot",
            "ongoing_action_behavior_class",
            "same_input_lock_remaining",
            "swap_lock_remaining",
            "action_end_remaining",
            "pending_packet_count",
            "next_packet_time_remaining",
            "last_packet_time_remaining",
            "pending_packet_behavior_class",
            "pending_packet_effect_flags",
            "persistent_off_field_owner_slot",
            "persistence_cutoff_remaining",
            "character_reentry_remaining_by_slot",
        ],
        "raw_unbounded_packet_arrays_recommended": False,
        "training_allowed_under_v6_after_timing_patch": False,
        "search_allowed_under_v6_after_timing_patch": False,
        "conclusion": "v7_required_before_BC_PPO_Beam_MCTS",
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Candidate 124 timing Markov-state observation audit",
        "",
        f"Account observation remains `{report['observation_version']}` with shape `{report['observation_v6_shape']}`. It was not modified in Stage 1.",
        "",
        "The corrected runtime introduces hidden future-affecting state. Observation v7 is required before BC, PPO, Beam, or MCTS; training and search under v6 are blocked.",
        "",
        "| Runtime item | In v6 | Derivable | Risk | Recommended compact v7 field |",
        "|---|---:|---:|---|---|",
    ]
    for row in report["findings"]:
        lines.append(
            f"| {row['item']} | {str(row['present_in_v6_observation']).lower()} | "
            f"{str(row['derivable_from_current_observation_and_action_history']).lower()} | "
            f"{row['markov_aliasing_risk']} | `{row['recommended_v7_field_or_aggregation']}` |"
        )
    lines.extend([
        "",
        "Raw packet arrays must not be placed in the observation; use bounded counts, time summaries, behavior classes, and effect flags.",
        "",
        f"v6 labels SHA-256 before/after: `{report['observation_v6_labels_sha256_before']}` / `{report['observation_v6_labels_sha256_after']}`.",
        f"v6 deterministic initial-vector SHA-256 before/after: `{report['observation_v6_initial_vector_sha256_before']}` / `{report['observation_v6_initial_vector_sha256_after']}`.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    report = build_report()
    JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_REPORT.write_text(render_markdown(report), encoding="utf-8")
    print("timing_markov_state_observation_audit_v124 ok")


if __name__ == "__main__":
    main()

