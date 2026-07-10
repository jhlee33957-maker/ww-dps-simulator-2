# Mornye Source Alignment Review

## Summary

- Safe-to-patch candidates: 22.
- Review-only/blocking candidates: 6.
- Unresolved source rows retained: 46.

No candidate should be applied automatically by this audit script.

## Candidate Details

### Safe Review Candidates

- `mornye_basic_stage_1` coefficients: [0.5569] -> [0.1671, 0.2227, 0.1671]
- `mornye_basic_stage_1` timing: 0.4167 -> 1.0167
- `mornye_basic_stage_2` coefficients: [1.1932] -> [0.2386, 0.2386, 0.179, 0.179, 0.179, 0.179]
- `mornye_basic_stage_2` timing: 0.8167 -> 1.1333
- `mornye_basic_stage_3` coefficients: [1.034] -> [0.4136, 0.1034, 0.1034, 0.1034, 0.1034, 0.1034, 0.1034]
- `mornye_basic_stage_3` timing: 0.8333 -> 1.5167
- `mornye_basic_stage_4` timing: 1.9333 -> 2.8333
- `mornye_wfo_basic_stage_1` coefficients: [0.5568] -> [0.1392, 0.1392, 0.1392, 0.1392]
- `mornye_wfo_basic_stage_1` timing: 0.35 -> 0.7167
- `mornye_wfo_basic_stage_2` coefficients: [1.034] -> [0.2585, 0.2585, 0.2585, 0.2585]
- `mornye_wfo_basic_stage_2` timing: 0.7167 -> 1.1333
- `mornye_wfo_basic_stage_3` coefficients: [1.0342] -> [0.0931, 0.0931, 0.0931, 0.0931, 0.3309, 0.3309]
- `mornye_wfo_basic_stage_3` timing: 0.65 -> 1.0167
- `mornye_wfo_basic_stage_3` resource:concerto_energy_gain: 22.56 -> 20
- `mornye_heavy_attack_normal` coefficients: [0.37] -> [0.111, 0.111, 0.148]
- `mornye_heavy_attack_normal` timing: 1.5833 -> 2.3333
- `mornye_heavy_geopotential_shift` coefficients: [0.4414] -> [0.4414, 0.9902]
- `mornye_heavy_geopotential_shift` timing: 1.3333 -> 1.2
- `mornye_heavy_inversion` timing: 1.4333 -> 1.3
- `mornye_skill_optimal_solution` timing: 2.0167 -> 1.8333
- `mornye_skill_distributed_array` coefficients: [1.5908] -> [0.3977, 0.3977, 0.3977, 0.3977]
- `mornye_liberation_critical_protocol` timing: 4.7 -> 4.9333

### Review-Only / Out-of-Scope Candidates

- `mornye_intro_convergence` / timing: Source/current mismatch found in audit. Human review required before patching.
- `mornye_intro_convergence` / resource:concerto_energy_gain: Resource mismatch found in audit. Human review required before patching.
- `Syntony Field / High Syntony Field` / mechanic_scope: Future implementation needs dedicated scheduling design.
- `Tune Break / Interfered / Particle Jet` / mechanic_scope: Keep out of source-alignment patch; needs new mechanic design.
- `Proof of Boundedness, healing, DEF, defensive survival` / mechanic_scope: Out of scope for audit/source alignment.
- `Energy Regen scaling / advanced passives` / mechanic_scope: Review when team-buff/stat-scaling system is expanded.

## Exact/Close Matches

- `mornye_outro_recursion` coefficients=missing timing=exact
