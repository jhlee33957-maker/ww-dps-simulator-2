from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from rl.guarded_ppo import PRIOR_PPO_MODEL_PATH, PRIOR_PPO_SUMMARY_PATH, record_from_summary

    summary = json.loads((ROOT / PRIOR_PPO_SUMMARY_PATH).read_text(encoding="utf-8"))
    record = record_from_summary(
        summary,
        kind="prior_regressed_ppo_model",
        branch_id=None,
        chunk_index=0,
        cumulative_timesteps=100000,
        checkpoint_path=PRIOR_PPO_MODEL_PATH,
        summary_path=PRIOR_PPO_SUMMARY_PATH,
        timeline_path=Path("results/ppo_100k_timeline.csv"),
        externally_verified=False,
        immutable_model=True,
        declared_order=2,
    )
    assert record["selected_sequence_exact_match"] is False
    assert record["resolved_sequence_exact_match"] is False
    assert record["selected_sequence_agreement_count"] > 0
    assert record["resolved_sequence_agreement_count"] > 0
    assert 0.0 < record["selected_sequence_agreement_ratio"] < 1.0
    assert 0.0 < record["resolved_sequence_agreement_ratio"] < 1.0
    assert record["route_agreement_ratio_diagnostic_only"] > 0.0
    assert record["first_selected_action_divergence"]["zero_based_step"] == 4
    assert record["first_selected_action_divergence"]["baseline"] == "aemeath_resonance_skill"
    assert record["first_selected_action_divergence"]["candidate"] == "swap_to_mornye"
    assert not str(record["model_training_metadata_path"]).startswith("C:/Users/")
    print("guarded_ppo_route_diagnostics_smoke_test ok")


if __name__ == "__main__":
    main()
