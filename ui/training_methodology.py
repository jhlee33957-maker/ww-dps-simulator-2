from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from env.observation_features import OBSERVATION_VERSION
from simulator.roster import read_party_presets
from simulator.simulation import Simulation


def render_training_methodology(data_dir: Path, results_dir: Path) -> None:
    methodology = _load_json(data_dir / "rl_training_methodology.json") or _fallback_methodology()
    st.header("Training Methodology / RL 학습 방법")
    st.caption(f"Methodology version: {methodology.get('methodology_version', 'unknown')}")

    st.subheader("Objective / 목표")
    st.write(
        "The RL model optimizes 120s simulated DPS. Step reward is "
        "`damage_this_action / 10000.0`, and the final comparison metric is total damage / DPS "
        "over the normal 120s simulation."
    )

    st.subheader("Algorithm / 알고리즘")
    st.write(
        "Training uses MaskablePPO. Action masks prevent invalid actions such as cooldown-gated "
        "skills, resource-gated skills, unavailable swaps, and invalid state actions. "
        "Action masks prevent illegal moves but do not tell the agent the best route."
    )

    st.subheader("Lynae Curriculum / 커리큘럼")
    st.write(
        "Lynae has delayed payoff: Intro, Overflow, Spark Collision, Kaleidoscopic Parade, "
        "Polychrome Leap, True Color, Visual Impact, and Outro can require several valid choices "
        "before the reward becomes obvious. Aemeath can produce more immediate reward, so PPO may "
        "settle into an Aemeath local optimum."
    )
    st.write(
        "Curriculum reset modes expose PPO to Lynae branch states during training. "
        "curriculum reset is training-only; final evaluation default is none."
    )
    st.write(
        "Character/route-specific curriculum reset modes may exist for future delayed-payoff branches. "
        "They adjust training start states only; they do not modify damage formulas, cooldowns, "
        "action masks, final evaluation reward, or default evaluation reset."
    )
    st.json(methodology.get("curriculum_modes", {}))

    st.subheader("Route Demonstrations / BC Warm Start")
    st.write(
        "Route demonstrations and behavior-cloning warm-starts are training aids for long delayed-reward "
        "branches. They initialize the policy toward valid source-backed action sequences. "
        "Balanced demonstrations can include both baseline party routes and delayed branch routes, and "
        "small BC refresh stages can be interleaved between PPO fine-tuning stages. They do not change simulator "
        "damage formulas, cooldowns, action masks, final evaluation reward, or final evaluation reset. "
        "They do not add character-specific usage reward bonuses, and the same mechanism can be used for "
        "future characters or party branches."
    )
    if methodology.get("route_demonstration_warm_start"):
        st.json(methodology["route_demonstration_warm_start"])

    st.subheader("What Curriculum Does Not Mean / 커리큘럼이 바꾸지 않는 것")
    st.write(
        "It does not change Lynae damage, cooldowns, resources, transition actions, or action masks. "
        "No character-specific usage reward bonus is applied by default. "
        "기본 보상에는 특정 캐릭터를 사용했다는 이유만으로 주는 추가 점수가 없습니다. "
        "It does not change final evaluation conditions unless explicitly selected."
    )

    st.subheader("Trust And Limitations / 신뢰와 한계")
    st.write(
        "The model is not a mathematical proof of optimal rotation. It is an RL-discovered policy "
        "under the simulator's current assumptions."
    )
    for note in methodology.get("known_limitations", []):
        st.write(f"- {note}")
    st.warning(
        "old PPO models before Lynae fixes are stale; retrain or continue-training from a compatible "
        "checkpoint before comparing new Lynae results."
    )

    selected_party_id, sim = _render_party_metadata(data_dir)
    st.subheader("Current Metadata / 현재 메타데이터")
    st.write(
        {
            "observation_version": OBSERVATION_VERSION,
            "selected_party_preset": selected_party_id,
            "selected_party_members": sim.selected_party_character_ids if sim else [],
            "policy_action_count": len(sim.policy_actions) if sim else None,
            "evaluation_default": methodology.get("evaluation_default", "none"),
        }
    )

    _render_training_metadata(results_dir / "training_metadata.json", methodology)
    _render_evaluation_summary(results_dir / "ppo_evaluation_summary.json")


def _render_party_metadata(data_dir: Path) -> tuple[str | None, Simulation | None]:
    presets = read_party_presets(data_dir)
    if not presets:
        st.info("No party presets are available for current metadata display.")
        return None, None
    preset_ids = list(presets)
    selected_party_id = st.selectbox(
        "Party Preset",
        options=preset_ids,
        index=0,
        format_func=lambda preset_id: presets[preset_id].get("display_name", preset_id),
    )
    try:
        return selected_party_id, Simulation.from_json(data_dir, party=selected_party_id)
    except Exception as exc:
        st.warning(f"Could not load selected party metadata: {exc}")
        return selected_party_id, None


def _render_training_metadata(path: Path, methodology: dict[str, Any]) -> None:
    st.subheader("Training Artifact Metadata / 학습 결과 메타데이터")
    metadata = _load_json(path)
    if metadata is None:
        st.warning("results/training_metadata.json is missing. Training metadata may be unavailable or stale.")
        return
    keys = [
        "timesteps",
        "curriculum_reset_mode",
        "ent_coef",
        "learning_rate",
        "n_steps",
        "batch_size",
        "gamma",
        "seed",
        "model_path",
        "reward_formula",
        "evaluation_default_reset_mode",
        "methodology_summary_id",
        "old_model_invalidation_note",
    ]
    st.write({key: metadata.get(key) for key in keys})
    if metadata.get("methodology_summary_id") != methodology.get("methodology_summary_id"):
        st.warning("Training methodology metadata is missing or stale for the current UI methodology file.")


def _render_evaluation_summary(path: Path) -> None:
    st.subheader("Evaluation Summary / 평가 요약")
    summary = _load_json(path)
    if summary is None:
        st.info("results/ppo_evaluation_summary.json is missing. Run evaluation to populate action usage and damage breakdowns.")
        return
    st.write(
        {
            "curriculum_reset_mode": summary.get("curriculum_reset_mode", "none"),
            "unused_party_members": summary.get("unused_party_members"),
            "selected_action_counts": summary.get("selected_action_counts"),
            "resolved_action_counts": summary.get("resolved_action_counts"),
            "damage_by_character": summary.get("damage_by_character"),
        }
    )


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _fallback_methodology() -> dict[str, Any]:
    return {
        "methodology_version": "fallback",
        "methodology_summary_id": "fallback",
        "algorithm": "MaskablePPO",
        "reward_formula": "damage_this_action / 10000.0",
        "evaluation_default": "none",
        "curriculum_modes": {},
        "known_limitations": [
            "Single-target 120s simulator assumptions are simplified.",
            "Curriculum can help delayed-reward exploration but does not prove optimality.",
        ],
    }
