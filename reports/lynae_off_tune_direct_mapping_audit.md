# Lynae Off-Tune Direct Mapping Audit

Mapping file: `data\source\lynae_off_tune_direct_mapping_v80.json`
Source workbook: `鸣潮动作数据汇总(5).xlsx`
Source sheet/column: `角色-女` `S (偏谐值)`

## Counts
- Action records: `43`
- Confirmed source-backed actions: `37`
- Confirmed selectors: `5`
- Unresolved: `1` (`lynae_echo_hyvatia`)

## Records
| action_id | value | source | status | mapping | alias_of |
| --- | ---: | --- | --- | --- | --- |
| `lynae_basic_stage_1` | `40.8` | `角色-女!S2577` | `workbook_confirmed` | `single` | `` |
| `lynae_basic_stage_2` | `74.4` | `角色-女!S2578:S2580` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_basic_stage_3` | `58.4` | `角色-女!S2581` | `workbook_confirmed` | `single` | `` |
| `lynae_dodge_counter` | `65.6` | `角色-女!S2582` | `workbook_confirmed` | `single` | `` |
| `lynae_mid_air_attack` | `68.0` | `角色-女!S2583:S2584` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_spark_collision_lv1` | `52.6` | `角色-女!S2586:S2587` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_spark_collision_lv2` | `157.8` | `角色-女!S2588:S2589` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_spark_collision_lv3` | `263.0` | `角色-女!S2590:S2591` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_basic_stage_1` | `39.2` | `角色-女!S2592:S2594` | `workbook_confirmed_mode_representative` | `mutually_exclusive_timing_variant` | `` |
| `lynae_kaleidoscopic_dodge_counter` | `39.2` | `角色-女!S2595` | `workbook_confirmed` | `single` | `` |
| `lynae_kaleidoscopic_basic_stage_2` | `36.8` | `角色-女!S2596:S2597` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_basic_stage_3` | `53.61` | `角色-女!S2598:S2600` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_basic_stage_4` | `70.4` | `角色-女!S2602:S2605` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_basic_stage_5` | `119.24` | `角色-女!S2611:S2614` | `workbook_confirmed_repeat_aware` | `repeat_aware` | `` |
| `lynae_kaleidoscopic_mid_air_attack` | `68.0` | `角色-女!S2615:S2616` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_ground_heavy_hold` | `58.45` | `角色-女!S2617:S2623` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_kaleidoscopic_graffiti_blast` | `49.6` | `角色-女!S2624` | `workbook_confirmed` | `single` | `` |
| `lynae_kaleidoscopic_mid_air_heavy` | `115.22` | `角色-女!S2633:S2639` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_polychrome_leap_stage_1` | `48.0` | `角色-女!S2643:S2645` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_polychrome_leap_stage_2` | `48.0` | `角色-女!S2649:S2650` | `workbook_confirmed_repeat_aware_mode_variant` | `repeat_aware_mode_variant` | `` |
| `lynae_polychrome_leap_stage_3` | `31.0` | `角色-女!S2660:S2661` | `workbook_confirmed_repeat_aware` | `repeat_aware` | `` |
| `lynae_resonance_skill_palette` | `87.22` | `角色-女!S2663:S2666` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_resonance_skill_additive_color` | `72.8` | `角色-女!S2673:S2674` | `workbook_confirmed_summed_from_rows` | `sum_rows` | `` |
| `lynae_iridescent_splash` | `68.0` | `角色-女!S2677:S2678` | `workbook_confirmed_mode_representative` | `mutually_exclusive_mode_variant` | `` |
| `lynae_visual_impact` | `609.6` | `角色-女!S2680:S2682` | `workbook_confirmed_mode_representative` | `mutually_exclusive_mode_variant` | `` |
| `lynae_intro_time_to_show_some_colors` | `106.4` | `角色-女!S2689:S2691` | `workbook_confirmed_repeat_aware_mode_variant` | `repeat_aware_mode_variant` | `` |
| `lynae_resonance_liberation_prismatic_overblast` | `480.0` | `角色-女!S2695` | `workbook_confirmed_repeat_aware` | `repeat_aware` | `` |
| `lynae_to_a_vivid_tomorrow` | `171.28` | `角色-女!S2697:S2698` | `workbook_confirmed_repeat_aware` | `repeat_aware` | `` |
| `lynae_outro_lets_hit_the_road` | `0.0` | `角色-女!S2700:S2701` | `workbook_confirmed_zero` | `workbook_confirmed_zero` | `` |
| `lynae_tune_break` | `0.0` | `角色-女!S2704` | `workbook_confirmed_zero` | `workbook_confirmed_zero` | `` |
| `lynae_tune_response_spectral_analysis` | `0.0` | `角色-女!S2735` | `workbook_confirmed_zero` | `workbook_confirmed_zero` | `` |
| `lynae_polychrome_leap_stage_1_c1` | `48.0` | `角色-女!S2643:S2645` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_polychrome_leap_stage_1` |
| `lynae_polychrome_leap_stage_2_c1` | `48.0` | `角色-女!S2649:S2650` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_polychrome_leap_stage_2` |
| `lynae_polychrome_leap_stage_3_c1` | `31.0` | `角色-女!S2660:S2661` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_polychrome_leap_stage_3` |
| `lynae_iridescent_splash_c3` | `68.0` | `角色-女!S2677:S2678` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_iridescent_splash` |
| `lynae_visual_impact_c3` | `609.6` | `角色-女!S2680:S2682` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_visual_impact` |
| `lynae_resonance_liberation_prismatic_overblast_c5` | `480.0` | `角色-女!S2695` | `workbook_confirmed_internal_alias` | `constellation_same_action_rows` | `lynae_resonance_liberation_prismatic_overblast` |
| `lynae_basic_attack` | `0.0` | `None` | `non_damaging_selector` | `non_damaging_selector` | `` |
| `lynae_spark_collision` | `0.0` | `None` | `non_damaging_selector` | `non_damaging_selector` | `` |
| `lynae_resonance_skill` | `0.0` | `None` | `non_damaging_selector` | `non_damaging_selector` | `` |
| `lynae_resonance_liberation` | `0.0` | `None` | `non_damaging_selector` | `non_damaging_selector` | `` |
| `lynae_polychrome_leap` | `0.0` | `None` | `non_damaging_selector` | `non_damaging_selector` | `` |
| `lynae_echo_hyvatia` | `0.0` | `声骸!371` | `unresolved_echo_off_tune` | `unresolved_echo_off_tune` | `` |
