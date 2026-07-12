# Manual 120s BC Demonstration Candidate 106

- Candidate status: pending external review
- Source verified baseline: 105
- Dataset: `data/generated/manual_120s_bc_demonstration_v105.npz`
- Dataset SHA-256: `b020a1b9309b46bd87eb3fff4837aead53035c4c84620962f47feb9fc11846ff`
- Samples: 148 across 1 episode
- Observation: slot_generic_mechanics_v5 / [314]
- Policy actions: 25 (max slots 32)
- Selected hash: `e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1`
- Resolved hash: `3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229`
- Final combat time: 120.0
- Total damage: 5165134.682363359
- DPS: 43042.78901969466
- Total reward: 516.5134682363359
- Action data hash: `d6377d54a1abb985dc5f58866321c61c7b904a6b73ddc1538be7e38d36a99ff1`
- Party config hash: `bd106ba1c0f5581436c35fea736a00fd6ad92b131f8b43ba8cf1e3dc89cbcb11`
- Direct action manifest SHA-256: `ed8bda448ce1d74cf34208e90a0d4dc8b21214197309e28a8c5ca53a6be8eb6d`

## Arrays

- `observations`: dtype `float32`, shape `[148, 314]`
- `action_indices`: dtype `int64`, shape `[148]`
- `action_ids`: dtype `<U28`, shape `[148]`
- `action_masks`: dtype `bool`, shape `[148, 25]`
- `resolved_action_ids`: dtype `<U47`, shape `[148]`
- `active_characters`: dtype `<U7`, shape `[148]`
- `rewards`: dtype `float64`, shape `[148]`
- `damages`: dtype `float64`, shape `[148]`
- `combat_time_costs`: dtype `float64`, shape `[148]`
- `combat_times_before`: dtype `float64`, shape `[148]`
- `combat_times_after`: dtype `float64`, shape `[148]`
- `action_times_before`: dtype `float64`, shape `[148]`
- `action_times_after`: dtype `float64`, shape `[148]`
- `episode_ids`: dtype `<U31`, shape `[148]`
- `step_indices`: dtype `int64`, shape `[148]`
- `terminated`: dtype `bool`, shape `[148]`
- `truncated`: dtype `bool`, shape `[148]`
- `remaining_returns`: dtype `float64`, shape `[148]`
- `remaining_damage`: dtype `float64`, shape `[148]`
- `observation_versions`: dtype `<U25`, shape `[148]`
- `action_data_hashes`: dtype `<U64`, shape `[148]`
- `party_config_hashes`: dtype `<U64`, shape `[148]`
- `route_ids`: dtype `<U24`, shape `[148]`
- `metadata_json`: dtype `<U4557`, shape `[]`

## Validation

- Contract validation: ok
- Replay validation: ok
- Alias audit: 148 unique observation+mask keys, 0 conflicts
- Legacy stale demos rejected: 2

## BC Small-Overfit Smoke

- Status: ok
- initial_masked_nll: 1.755488395690918
- final_masked_nll: 0.006889711134135723
- nll_decrease: 1.7485986845567822
- final_top1_accuracy: 1.0
- invalid_top1_count: 0

## Training Boundary

- Full BC training was not executed.
- Long PPO training was not executed.
- Remaining return, remaining damage, step index, route ID, episode ID, and resolved action ID are diagnostics only and are not part of the 314-dimensional observation.

## Post-Review Commands

```powershell
.\.venv\Scripts\python.exe rl\pretrain_maskable_ppo_bc.py `
  --party aemeath_mornye_lynae_enabled_test_party `
  --initial-active-character aemeath `
  --demo-path data\generated\manual_120s_bc_demonstration_v105.npz `
  --model-path models\maskable_ppo_bc_v105.zip `
  --epochs 300 `
  --batch-size 148 `
  --learning-rate 0.003 `
  --seed 11 `
  --device cpu
```

```powershell
.\.venv\Scripts\python.exe rl\evaluate_maskable_ppo.py `
  --model-path models\maskable_ppo_bc_v105.zip `
  --party aemeath_mornye_lynae_enabled_test_party `
  --initial-active-character aemeath
```

```powershell
.\.venv\Scripts\python.exe rl\train_maskable_ppo.py `
  --party aemeath_mornye_lynae_enabled_test_party `
  --initial-active-character aemeath `
  --curriculum-reset-mode none `
  --load-model models\maskable_ppo_bc_v105.zip `
  --model-path models\maskable_ppo_candidate_after_bc_v105.zip `
  --timesteps 100000 `
  --seed 42
```

