# RL Training Methodology

Methodology version: `2026-07-09-lynae-curriculum-v1`

The training algorithm is MaskablePPO. The objective is to maximize simulated 120s damage, and the step reward remains `damage_this_action / 10000.0`. Final comparisons should use total damage and DPS over the normal 120s simulation.

Action masks prevent invalid policy choices such as cooldown-gated skills, resource-gated skills, unavailable swaps, and state-invalid actions. They prevent illegal moves, but they do not tell the policy which valid route is best.

Curriculum reset is training-only. Character/route-specific curriculum reset modes may exist for delayed-payoff branches. They adjust training start states only. They do not modify damage formulas, cooldowns, action masks, final evaluation reward, or default evaluation reset. No character-specific usage reward bonus is applied by default.

Route demonstrations and behavior-cloning warm-starts are also training aids. They initialize the policy toward valid source-backed action sequences for long delayed-reward branches. Balanced demonstrations can include both baseline party routes and delayed branch routes so BC does not overgeneralize toward immediate branch entry. Small BC refresh stages can be interleaved between PPO fine-tuning stages to reduce delayed-branch forgetting. They do not change simulator damage formulas, cooldowns, action masks, final evaluation reward, or final evaluation reset. They do not add character-specific usage reward bonuses, and demonstrations can be added for any future character or party branch.

The final evaluation default is none: use `curriculum_reset_mode = none` for fair 120s comparisons unless intentionally studying curriculum-start behavior.

Known limitations:
- The model is an RL-discovered policy, not a mathematical proof of optimal rotation.
- The simulator is a single-target 120s Endgame Matrix-style approximation.
- Movement, stamina, continuous positioning, and some animation-cancel details are simplified.
- Long delayed-reward branches may still require curriculum, entropy, longer training, macro actions, or additional diagnostics.

Old PPO models before Lynae fixes are stale. Models trained before the Lynae transition, observation, reward exposure, and source-ref fixes should not be compared with new results without retraining or compatible continue-training.

Recommended next training sequence:
- Stage 0: generate balanced route demonstrations with `scripts/generate_route_demonstrations.py --route-set aemeath_mornye_lynae_balanced_route_warm_start_v2`, then run `rl/pretrain_maskable_ppo_bc.py` to create a BC warm-start checkpoint.
- Stage 1: use `rl/train_maskable_ppo_bc_refresh_plan.py` to alternate `mixed_lynae_route_curriculum` PPO cycles with small BC refresh stages.
- Stage 2 final: short `curriculum_reset_mode = none` PPO fine-tune from the last refreshed checkpoint.
- Final evaluation: `curriculum_reset_mode = none` with `--diagnose-policy-probs`

This sequence is not guaranteed to make a delayed branch optimal. It gives PPO a fairer chance to learn the branch before returning to normal reset.
