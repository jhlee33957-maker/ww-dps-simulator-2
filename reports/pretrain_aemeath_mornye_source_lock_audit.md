# Pretrain Aemeath / Mornye Source-lock Audit

Overall status: **REVIEW_REQUIRED**
Workbook: `data\source\鸣潮动作数据汇总.xlsx`

## Sections

| Status | Section | Mismatches | Review required |
| --- | --- | ---: | ---: |
| PASS | Aemeath Forte / Seraphic Duet Tune Rupture Follow-up | 0 | 0 |
| PASS | Aemeath Overdrive / Forte Enhancement State | 0 | 0 |
| PASS | Aemeath Mech Basic Stage 3 Repeat-aware Correction | 0 | 0 |
| PASS | Aemeath Tune Break and Starburst | 0 | 0 |
| PASS | Mornye Relative Momentum / Rest Mass Energy | 0 | 0 |
| REVIEW_REQUIRED | Mornye Baseline Rest Mass Energy | 0 | 4 |
| REVIEW_REQUIRED | Mornye Heavy Geopotential Shift / Syntony Field | 0 | 1 |
| REVIEW_REQUIRED | Mornye High Syntony / Critical Protocol | 0 | 1 |
| PASS | Mornye Interfered Marker | 0 | 0 |
| PASS | Mornye Tune Break / Particle Jet | 0 | 0 |

## Mismatches

- None.

## Review Required

- [mornye_baseline_rest_mass] mornye_basic_stage_1 has current resource value but no explicit source_rows metadata in data/actions.json.
- [mornye_baseline_rest_mass] mornye_basic_stage_2 has current resource value but no explicit source_rows metadata in data/actions.json.
- [mornye_baseline_rest_mass] mornye_basic_stage_3 has current resource value but no explicit source_rows metadata in data/actions.json.
- [mornye_baseline_rest_mass] mornye_basic_stage_4 has current resource value but no explicit source_rows metadata in data/actions.json.
- [mornye_geopotential_syntony] Syntony Field Off-Tune +50% is workbook text confirmed; exact field tick/heal behavior remains simulator interpretation.
- [mornye_high_syntony_critical_protocol] High Syntony inherited Off-Tune +50% and healing proxy are documented simulator interpretations where exact separate source timing is not modeled.

## Workbook Rows Checked

- Aemeath: 角色-女!2786, 角色-女!2787, 角色-女!2793, 角色-女!2796, 角色-女!2806, 角色-女!2889:2892, 角色-女!2931, 角色-女!2932, dmg!2578, dmg!2579, dmg!2590, dmg!2628, dmg!2629
- Mornye: 角色-女!4128, 角色-女!4129, 角色-女!4132, 角色-女!4133, 角色-女!4135, 角色-女!4136, 角色-女!4144:4147, 角色-女!4150, 角色-女!4151, 角色-女!4154, 角色-女!4164, 角色-女!4181, 角色-女!4185, dmg!2532

## Non-workbook / User-supplied Sources

- `aemeath:aemeath_real_manual`: user_profile (user_supplied_required) in data/build_profiles.json
- `aemeath:aemeath_user_real_01`: user_profile (user_supplied_required) in data/build_profiles.json
- `mornye:mornye_real_manual`: user_profile (user_supplied_required) in data/build_profiles.json
- `mornye:mornye_user_real_01`: user_profile (user_supplied_required) in data/build_profiles.json
- `starfield_calibrator`: user_supplied_tooltip (user_supplied_weapon_tooltip) in data/weapons.json
- `discord`: user_supplied_tooltip (user_supplied_weapon_tooltip) in data/weapons.json
- `everbright_polestar`: user_supplied_tooltip (user_supplied_weapon_tooltip) in data/weapons.json
- `mornye_halo_of_starry_radiance_5set`: user_supplied_tooltip_or_sim_interpretation (user_supplied_set_tooltip) in data/buffs.json
- `starfield_calibrator_party_crit_damage`: user_supplied_tooltip_or_sim_interpretation (user_supplied_weapon_tooltip) in data/buffs.json
- `everbright_polestar_liberation_penetration`: user_supplied_tooltip_or_sim_interpretation (user_supplied_weapon_tooltip) in data/buffs.json
- `aemeath_trailblazing_star_5set`: user_supplied_tooltip_or_sim_interpretation (user_supplied_set_tooltip) in data/buffs.json

## Intentionally Unresolved / Scaffolded

- Aemeath Fusion Burst / Fusion Trail generated damage scaffold remains unresolved.
- Aemeath C6 trail stack granting remains disabled for S0 default runtime.
- Full multi-target trail/Tune tracking remains unresolved.
- Exact Mornye Syntony Field heal tick timing remains unimplemented.
