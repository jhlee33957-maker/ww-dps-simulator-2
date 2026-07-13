# Off-Tune Value Mapping Audit

- Source: user-provided workbook, `角色-女` column S.
- Boss Tune Break cooldown: 3.0s from `附页2!B227` for COST4/red-name targets.
- Cooldown rule: Off-Tune accumulation is blocked entirely while Tune Break cooldown is active.
- Mapping rule: sum column S across separate workbook rows mapped to one simulator action; apply repeat-aware expansion only when a workbook frame-row repeat note is explicitly confirmed for the action.
- Damaging actions checked: 40.
- Mapped action count: 42.
- Unresolved damaging action ids: none.
- Internal alias action ids: ['aemeath_form_switch_to_aemeath_after_overdrive', 'aemeath_form_switch_to_aemeath_normal', 'aemeath_form_switch_to_mech_normal'].

## Completeness Guard Patch

- Actions with missing Off-Tune metadata before patch: ['aemeath_form_switch_to_mech_normal', 'aemeath_form_switch_to_aemeath_normal', 'aemeath_form_switch_to_aemeath_after_overdrive', 'aemeath_seraphic_duet_encore'].
- Actions with missing Off-Tune metadata after patch: none.
- Completeness status: `complete`.

| Action | Final Status | Off-Tune | Source Status | Source Ref | Alias Of |
|---|---|---:|---|---|---|
| `aemeath_form_switch_to_mech_normal` | `fixed_internal_alias` | 13.34 | `workbook_confirmed_internal_alias` | `角色-女!S2886` | `aemeath_mech_basic_stage_1` |
| `aemeath_form_switch_to_aemeath_normal` | `fixed_internal_alias` | 26.64 | `workbook_confirmed_internal_alias` | `角色-女!S2739` | `aemeath_basic_form_stage_1` |
| `aemeath_form_switch_to_aemeath_after_overdrive` | `fixed_internal_alias` | 39.93 | `workbook_confirmed_internal_alias` | `角色-女!S2740:S2742` | `aemeath_basic_form_stage_2` |
| `aemeath_seraphic_duet_encore` | `fixed_workbook_confirmed` | 128.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S2925:S2929` |  |

## Key Corrections

- `mornye_heavy_geopotential_shift`: 29.6 from `角色-女!S4117`.
- `mornye_heavy_inversion`: 104.0 from `角色-女!S4136`.
- `aemeath_mech_basic_stage_3`: 62.54 repeat-aware Off-Tune from `角色-女!S2889:S2892`, with A3-2 repeated by `角色-女!D2890`.
- `aemeath_seraphic_duet_encore`: 128.0 from `角色-女!S2925:S2929`.

## Notes

- Internal aliases copy source workbook Off-Tune metadata without changing damage/timing/resource behavior.
- Mornye Syntony Field Damage 1 deals damage but has a source-confirmed Off-Tune contribution of 0. Its repeated executions are supplied by the scheduled-effect engine.
- Mornye Syntony Field Damage 2 is the non-QTE target-position deployment event and owns the source-confirmed Off-Tune contribution of 66.4.

## Mappings

| Action | Off-Tune | Source Status | Source Ref | Alias Of |
|---|---:|---|---|---|
| `aemeath_basic_form_stage_1` | 26.64 | `workbook_confirmed` | `角色-女!S2739` |  |
| `aemeath_basic_form_stage_2` | 39.93 | `workbook_confirmed_summed_from_rows` | `角色-女!S2740:S2742` |  |
| `aemeath_basic_form_stage_3` | 53.55 | `workbook_confirmed_summed_from_rows` | `角色-女!S2743:S2747` |  |
| `aemeath_basic_form_stage_4` | 65.76 | `workbook_confirmed_summed_from_rows` | `角色-女!S2753:S2755` |  |
| `aemeath_form_switch_to_aemeath_after_overdrive` | 39.93 | `workbook_confirmed_internal_alias` | `角色-女!S2740:S2742` | `aemeath_basic_form_stage_2` |
| `aemeath_form_switch_to_aemeath_normal` | 26.64 | `workbook_confirmed_internal_alias` | `角色-女!S2739` | `aemeath_basic_form_stage_1` |
| `aemeath_form_switch_to_mech_normal` | 13.34 | `workbook_confirmed_internal_alias` | `角色-女!S2886` | `aemeath_mech_basic_stage_1` |
| `aemeath_heavenfall_finale` | 840.0 | `workbook_confirmed` | `角色-女!S2801` |  |
| `aemeath_heavy_aemeath_charged_1` | 53.37 | `workbook_confirmed_summed_from_rows` | `角色-女!S2761:S2762` |  |
| `aemeath_heavy_aemeath_charged_2` | 120.03 | `workbook_confirmed_summed_from_rows` | `角色-女!S2765:S2767` |  |
| `aemeath_heavy_mech_charged_1` | 53.36 | `workbook_confirmed` | `角色-女!S2904` |  |
| `aemeath_heavy_mech_charged_2` | 133.36 | `workbook_confirmed` | `角色-女!S2907` |  |
| `aemeath_liberation_overdrive` | 392.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S2796:S2797` |  |
| `aemeath_mech_basic_stage_1` | 13.34 | `workbook_confirmed` | `角色-女!S2886` |  |
| `aemeath_mech_basic_stage_2` | 53.37 | `workbook_confirmed_summed_from_rows` | `角色-女!S2887:S2888` |  |
| `aemeath_mech_basic_stage_3` | 62.54 | `workbook_confirmed_repeat_aware` | `角色-女!S2889:S2892` |  |
| `aemeath_mech_basic_stage_4` | 77.37 | `workbook_confirmed_summed_from_rows` | `角色-女!S2897:S2898` |  |
| `aemeath_qte_intro_human` | 77.37 | `workbook_confirmed_summed_from_rows` | `角色-女!S2790:S2792` |  |
| `aemeath_qte_intro_mech` | 93.85 | `workbook_confirmed_summed_from_rows` | `角色-女!S2935:S2936` |  |
| `aemeath_seraphic_duet_encore` | 128.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S2925:S2929` |  |
| `aemeath_seraphic_duet_overturn` | 52.01 | `workbook_confirmed_summed_from_rows` | `角色-女!S2780:S2783` |  |
| `aemeath_sync_strike_armament_merge` | 77.37 | `workbook_confirmed_summed_from_rows` | `角色-女!S2773:S2775` |  |
| `aemeath_sync_strike_call_of_dawn` | 93.86 | `workbook_confirmed_summed_from_rows` | `角色-女!S2917:S2920` |  |
| `aemeath_tune_break` | 0.0 | `workbook_confirmed_tune_break_rows_zero` | `角色-女!S2804:S2805` |  |
| `mornye_basic_stage_1` | 28.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S4102:S4104` |  |
| `mornye_basic_stage_2` | 33.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S4105:S4107` |  |
| `mornye_basic_stage_3` | 26.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S4108:S4109` |  |
| `mornye_basic_stage_4` | 68.0 | `workbook_confirmed` | `角色-女!S4110` |  |
| `mornye_heavy_attack_normal` | 24.8 | `workbook_confirmed_summed_from_rows` | `角色-女!S4114:S4116` |  |
| `mornye_heavy_geopotential_shift` | 29.6 | `workbook_confirmed` | `角色-女!S4117` |  |
| `mornye_heavy_inversion` | 104.0 | `workbook_confirmed` | `角色-女!S4136` |  |
| `mornye_intro_convergence` | 136.0 | `workbook_confirmed` | `角色-女!S4149` |  |
| `mornye_liberation_critical_protocol` | 720.0 | `workbook_confirmed_mode_representative` | `角色-女!S4153/S4154` |  |
| `mornye_skill_distributed_array` | 80.0 | `workbook_confirmed_summed_from_rows` | `角色-女!S4144:S4147` |  |
| `mornye_skill_expectation_error` | 0.0 | `not_found_or_non_damaging` | `角色-女!S4137` |  |
| `mornye_skill_optimal_solution` | 90.4 | `workbook_confirmed` | `角色-女!S4142` |  |
| `mornye_syntony_field_damage` | 0.0 | `workbook_confirmed_zero_for_damage_1` | `角色-女!4126` |  |
| `mornye_syntony_field_target_damage` | 66.4 | `workbook_confirmed` | `角色-女!4127` |  |
| `mornye_tune_break` | 0.0 | `workbook_confirmed_tune_break_rows_zero` | `角色-女!S4157:S4159` |  |
| `mornye_wfo_basic_stage_1` | 7.0 | `workbook_confirmed` | `角色-女!S4128` |  |
| `mornye_wfo_basic_stage_2` | 13.0 | `workbook_confirmed` | `角色-女!S4129` |  |
| `mornye_wfo_basic_stage_3` | 30.68 | `workbook_confirmed_summed_from_rows` | `角色-女!S4131:S4134` |  |
