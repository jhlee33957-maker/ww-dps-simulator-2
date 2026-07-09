# RL Training Methodology

Methodology version: `2026-07-09-lynae-curriculum-v1`

The training algorithm is MaskablePPO. The objective is to maximize simulated 120s damage, and the step reward remains `damage_this_action / 10000.0`. Final comparisons should use total damage and DPS over the normal 120s simulation.

Action masks prevent invalid policy choices such as cooldown-gated skills, resource-gated skills, unavailable swaps, and state-invalid actions. They prevent illegal moves, but they do not tell the policy which valid route is best.

Curriculum reset is training-only. Character/route-specific curriculum reset modes may exist for delayed-payoff branches. They adjust training start states only. They do not modify damage formulas, cooldowns, action masks, final evaluation reward, or default evaluation reset. No character-specific usage reward bonus is applied by default.

The final evaluation default is none: use `curriculum_reset_mode = none` for fair 120s comparisons unless intentionally studying curriculum-start behavior.

Known limitations:
- The model is an RL-discovered policy, not a mathematical proof of optimal rotation.
- The simulator is a single-target 120s Endgame Matrix-style approximation.
- Movement, stamina, continuous positioning, and some animation-cancel details are simplified.
- Long delayed-reward branches may still require curriculum, entropy, longer training, macro actions, or additional diagnostics.

Old PPO models before Lynae fixes are stale. Models trained before the Lynae transition, observation, reward exposure, and source-ref fixes should not be compared with new results without retraining or compatible continue-training.

Recommended next training sequence:
- Stage 1: `curriculum_reset_mode = lynae_kaleidoscopic_ready_after_liberation`, `timesteps = 100000`, `ent_coef = 0.04`
- Stage 2: `curriculum_reset_mode = lynae_after_intro_liberation_used`, load Stage 1, `timesteps = 100000`, `ent_coef = 0.03`
- Stage 3: `curriculum_reset_mode = aemeath_post_liberation_ready_for_lynae`, load Stage 2, `timesteps = 100000`, `ent_coef = 0.02`
- Stage 4: `curriculum_reset_mode = mixed_lynae_route_curriculum`, load Stage 3, `timesteps = 200000`, `ent_coef = 0.02`
- Stage 5 final: `curriculum_reset_mode = none`, load Stage 4, `timesteps = 300000`, `ent_coef = 0.01`
- Final evaluation: `curriculum_reset_mode = none` with `--diagnose-policy-probs`

This sequence is not guaranteed to make a delayed branch optimal. It gives PPO a fairer chance to learn the branch before returning to normal reset.
