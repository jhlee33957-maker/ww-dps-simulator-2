# RL Training Methodology

Methodology version: `2026-07-09-lynae-curriculum-v1`

The training algorithm is MaskablePPO. The objective is to maximize simulated 120s damage, and the step reward remains `damage_this_action / 10000.0`. Final comparisons should use total damage and DPS over the normal 120s simulation.

Action masks prevent invalid policy choices such as cooldown-gated skills, resource-gated skills, unavailable swaps, and state-invalid actions. They prevent illegal moves, but they do not tell the policy which valid route is best.

Curriculum reset is training-only. It can start PPO from Aemeath-ready, Lynae-after-Intro, or Lynae-Kaleidoscopic states so delayed Lynae payoff is explored more often. It does not change Lynae damage, cooldowns, resources, source refs, action masks, or transition mechanics. It does not add a manual use-Lynae reward bonus.

The final evaluation default is none: use `curriculum_reset_mode = none` for fair 120s comparisons unless intentionally studying curriculum-start behavior.

Known limitations:
- The model is an RL-discovered policy, not a mathematical proof of optimal rotation.
- The simulator is a single-target 120s Endgame Matrix-style approximation.
- Movement, stamina, continuous positioning, and some animation-cancel details are simplified.
- Long delayed-reward branches may still require curriculum, entropy, longer training, macro actions, or additional diagnostics.

Old PPO models before Lynae fixes are stale. Models trained before the Lynae transition, observation, reward exposure, and source-ref fixes should not be compared with new results without retraining or compatible continue-training.
