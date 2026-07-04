# Mornye Excel Audit

## Summary

- Source character: `莫宁`.
- Workbook: `C:\Users\coree\OneDrive\Documents\GitHub\ww-dps-simulator-2\ww-dps-simulator-2\data\source\鸣潮动作数据汇总.xlsx`.
- Extracted source rows: 109.
- Action comparisons: 16.
- Unresolved/review-only rows: 46.
- Safe-to-patch candidates emitted: 0.

This is an audit-only artifact. It does not modify Mornye gameplay values, transition behavior, PPO reward logic, Beam Search, or RL training.

## Current Mornye v1 scope

- Implemented: baseline/Wide Field Observation routing, Rest Mass Energy, Relative Momentum, Geopotential Shift, Inversion, simplified skills, Critical Protocol, and Outro Recursion buff.
- Review-only or simplified: Intro Convergence, Syntony Field damage scheduling, High Syntony Field details, Energy Regen/passive scaling.
- Not implemented: Tune Break, Interfered Marker, Particle Jet response, Proof of Boundedness, healing, DEF, and full defensive systems.

## Action comparison table

| Action | Category | Coefficients | Timing | Source rows | Notes |
| --- | --- | --- | --- | --- | --- |
| `mornye_basic_stage_1` | basic | exact | exact | 角色-女!4102, 角色-女!4103, 角色-女!4104, 角色技能类型!2640, 角色技能类型!2641, 角色技能类型!2642 |  |
| `mornye_basic_stage_2` | basic | exact | exact | 角色-女!4105, 角色-女!4106, 角色-女!4107, 角色技能类型!2643, 角色技能类型!2644, 角色技能类型!2645 |  |
| `mornye_basic_stage_3` | basic | exact | exact | 角色-女!4108, 角色-女!4109, 角色技能类型!2646, 角色技能类型!2647 |  |
| `mornye_basic_stage_4` | basic | exact | exact | 角色-女!4110, 角色技能类型!2648 |  |
| `mornye_wfo_basic_stage_1` | wfo_basic | exact | exact | 角色-女!4128, 角色技能类型!2657 |  |
| `mornye_wfo_basic_stage_2` | wfo_basic | exact | exact | 角色-女!4129, 角色技能类型!2658 |  |
| `mornye_wfo_basic_stage_3` | wfo_basic | exact | exact | 角色-女!4131, 角色-女!4132, 角色-女!4133, 角色-女!4134, 角色技能类型!2660, 角色技能类型!2661, 角色技能类型!2662, 角色技能类型!2663 | Passive workbook text grants 20 Concerto after Observation A3. |
| `mornye_heavy_attack_normal` | heavy | exact | exact | 角色-女!4114, 角色-女!4115, 角色-女!4116, 角色技能类型!2651, 角色技能类型!2652, 角色技能类型!2653 |  |
| `mornye_heavy_geopotential_shift` | heavy | exact | exact | 角色-女!4117, 角色-女!4127, 角色技能类型!2654, 角色技能类型!2656 |  |
| `mornye_heavy_inversion` | heavy | exact | exact | 角色-女!4136, 角色技能类型!2664 |  |
| `mornye_skill_optimal_solution` | resonance_skill | exact | exact | 角色-女!4142, 角色技能类型!2665 | E1 pre/GP/parry rows are retained as unresolved review rows. |
| `mornye_skill_distributed_array` | resonance_skill | exact | exact | 角色-女!4143, 角色-女!4144, 角色-女!4145, 角色-女!4146, 角色-女!4147, 角色技能类型!2666, 角色技能类型!2667, 角色技能类型!2668, 角色技能类型!2669 |  |
| `mornye_liberation_critical_protocol` | resonance_liberation | exact | exact | 角色-女!4150, 角色-女!4153, 角色-女!4154, 角色技能类型!2671 | C5 and cinematic/time-stop rows are audit-only and not modeled. |
| `mornye_syntony_field_damage` | syntony_field | exact | source_missing | 角色-女!4126, 角色技能类型!2655 | Action exists as reviewed optional field damage; automatic scheduling is out of scope. |
| `mornye_intro_convergence` | intro_outro | exact | exact | 角色-女!4148, 角色-女!4149, 角色技能类型!2670 | Implemented incoming transition event; disabled by default through transition config. |
| `mornye_outro_recursion` | intro_outro | missing | exact | 角色-女!4164 | Workbook passive text: team all-damage amplification 25% after Outro. |

## Resource comparison table

| Action | Resource | Source | Current | Status |
| --- | --- | --- | --- | --- |
| `mornye_basic_stage_1` | `mechanic_effects.rest_mass_energy_delta` | `20` | `20` | exact |
| `mornye_basic_stage_2` | `mechanic_effects.rest_mass_energy_delta` | `43` | `43` | exact |
| `mornye_basic_stage_3` | `mechanic_effects.rest_mass_energy_delta` | `37` | `37` | exact |
| `mornye_basic_stage_4` | `mechanic_effects.rest_mass_energy_delta` | `100` | `100` | exact |
| `mornye_wfo_basic_stage_1` | `mechanic_effects.relative_momentum_delta` | `2.5` | `2.5` | exact |
| `mornye_wfo_basic_stage_2` | `mechanic_effects.relative_momentum_delta` | `3` | `3` | exact |
| `mornye_wfo_basic_stage_3` | `mechanic_effects.relative_momentum_delta` | `18` | `18` | exact |
| `mornye_wfo_basic_stage_3` | `concerto_energy_gain` | `20` | `20` | exact |
| `mornye_heavy_attack_normal` | `mechanic_effects.rest_mass_energy_delta` | `20` | `20` | exact |
| `mornye_heavy_geopotential_shift` | `mechanic_effects.rest_mass_energy_delta` | `-100` | `-100` | exact |
| `mornye_heavy_geopotential_shift` | `mechanic_effects.wide_field_observation_duration` | `30` | `30` | exact |
| `mornye_heavy_geopotential_shift` | `mechanic_effects.syntony_field_duration` | `25` | `25` | exact |
| `mornye_heavy_inversion` | `mechanic_effects.relative_momentum_delta` | `-100` | `-100` | exact |
| `mornye_heavy_inversion` | `mechanic_effects.observation_marker_duration` | `30` | `30` | exact |
| `mornye_skill_optimal_solution` | `cooldown` | `5` | `5` | exact |
| `mornye_skill_optimal_solution` | `mechanic_effects.rest_mass_energy_delta` | `100` | `100` | exact |
| `mornye_skill_distributed_array` | `cooldown` | `16` | `16` | exact |
| `mornye_skill_distributed_array` | `concerto_energy_gain` | `10` | `10` | exact |
| `mornye_skill_distributed_array` | `mechanic_effects.relative_momentum_delta` | `60` | `60` | exact |
| `mornye_liberation_critical_protocol` | `cooldown` | `25` | `25` | exact |
| `mornye_liberation_critical_protocol` | `resonance_energy_cost` | `175` | `175` | exact |
| `mornye_liberation_critical_protocol` | `concerto_energy_gain` | `20` | `20` | exact |
| `mornye_liberation_critical_protocol` | `mechanic_effects.high_syntony_field_duration` | `25` | `25` | exact |
| `mornye_syntony_field_damage` | n/a | n/a | n/a | no_resource_expectation |
| `mornye_intro_convergence` | `concerto_energy_gain` | `10` | `10` | exact |
| `mornye_intro_convergence` | `mechanic_effects.rest_mass_energy_delta` | `-100` | `-100` | exact |
| `mornye_intro_convergence` | `mechanic_effects.wide_field_observation_duration` | `30` | `30.0` | exact |
| `mornye_intro_convergence` | `mechanic_effects.syntony_field_duration` | `25` | `25.0` | exact |
| `mornye_outro_recursion` | `transition_config.action_time` | `0` | `0.0` | exact |
| `mornye_outro_recursion` | `buff.duration` | `30` | `30.0` | exact |
| `mornye_outro_recursion` | `buff.damage_amp_modifiers.all` | `0.25` | `0.25` | exact |

## Mechanics audit

| Mechanic | Status | Current behavior | Recommendation |
| --- | --- | --- | --- |
| Rest Mass Energy / Relative Momentum caps | implemented_v1 | characters/mornye.py tracks both resources and clamps to 100. | No audit candidate. |
| Baseline and Wide Field Observation combo routing | implemented_v1 | High-level policy actions resolve into baseline or WFO concrete actions. | Keep existing smoke coverage. |
| Geopotential Shift enters Wide Field Observation and creates Syntony Field | implemented_v1 | Concrete action consumes Rest Mass Energy, enters WFO, and records field duration metadata. | No gameplay patch from this audit. |
| Syntony Field / High Syntony Field | simplified_v1 | Durations are tracked as metadata; automatic field tick scheduling is not implemented. | Future implementation needs dedicated scheduling design. |
| Intro Convergence | implemented_but_disabled_by_default | Transition action applies Convergence damage/time and v1 WFO/Syntony effects only when Mornye intro mode is explicitly enabled. | Do not enable without a transition/QTE behavior task. |
| Outro Recursion | implemented_v1 | Transition config applies a 30s all-damage amp buff and consumes outgoing Concerto. | No audit candidate. |
| Tune Break / Interfered / Particle Jet | not_implemented_v1 | Only placeholder/review action metadata exists where applicable. | Keep out of source-alignment patch; needs new mechanic design. |
| Proof of Boundedness, healing, DEF, defensive survival | not_implemented_v1 | DPS simulator has no healing/DEF survival model for Mornye. | Out of scope for audit/source alignment. |
| Energy Regen scaling / advanced passives | simplified_v1 | Mornye support buff and direct action coefficients are modeled; scaling passives are not. | Review when team-buff/stat-scaling system is expanded. |

## Recommendations

- Treat all source-alignment candidates as review tasks; the extractor intentionally writes no gameplay JSON.
- Do not implement Tune/Interfered/Proof/healing/DEF from this audit. Those rows remain future-system evidence.
- Keep Intro/QTE disabled unless a separate transition behavior task enables and validates it.
- Re-run `python scripts/mornye_excel_audit_smoke_test.py` after workbook or Mornye data changes.
