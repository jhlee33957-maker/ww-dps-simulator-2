# Lynae Resource/Cooldown Alignment

Workbook: `data\source\鸣潮动作数据汇总.xlsx`
Source action/resource rows: `角色-女!2577:2738`

## Liberation Gating
- Lynae Prismatic Overblast (`lynae_resonance_liberation_prismatic_overblast`): Resonance Energy cost 125, cooldown 25s, cooldown group `lynae_resonance_liberation`.
- `lynae_resonance_liberation`: non-damaging policy selector with the same cost/cooldown metadata for guard visibility.
- `lynae_resonance_liberation_prismatic_overblast_c5`: disabled-by-default constellation variant with the same cost/cooldown guard.

## Resonance Skill Shared Cooldown
- `lynae_resonance_skill_palette` and `lynae_resonance_skill_additive_color` share cooldown group `lynae_resonance_skill` with user-confirmed cooldown 6.0s.

## Action Rows
| action_id | action rows | resonance gain | concerto gain | special resource | cost | cooldown | source_status | unresolved reason |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |
| `lynae_basic_stage_1` | `[2577]` | `1.28` | `4.59` | `{"source_core_gain_1": 12.0, "overflow_gain": 12.0}` | `0` | `0.0` | source_confirmed |  |
| `lynae_basic_stage_2` | `[2578, 2579, 2580]` | `2.34` | `8.37` | `{"source_core_gain_1": 21.0, "overflow_gain": 21.0}` | `0` | `0.0` | source_confirmed |  |
| `lynae_basic_stage_3` | `[2581]` | `1.83` | `6.57` | `{"source_core_gain_1": 17.0, "overflow_gain": 17.0}` | `0` | `0.0` | source_confirmed |  |
| `lynae_dodge_counter` | `[2582]` | `2.05` | `7.38` | `{"source_core_gain_1": 19.0, "overflow_gain": 19.0}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_mid_air_attack` | `[2583, 2584]` | `2.14` | `7.66` | `{"source_core_gain_1": 20.0, "overflow_gain": 20.0}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_spark_collision_lv1` | `[2586, 2587]` | `1.66` | `5.92` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_spark_collision_lv2` | `[2588, 2589]` | `4.94` | `17.76` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_spark_collision_lv3` | `[2590, 2591]` | `8.22` | `29.6` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_basic_stage_1` | `[2592, 2593, 2594]` | `1.23` | `4.41` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_dodge_counter` | `[2595]` | `1.23` | `4.41` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_basic_stage_2` | `[2596, 2597]` | `1.16` | `4.14` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_basic_stage_3` | `[2598, 2599, 2600]` | `1.68` | `6.03` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_basic_stage_4` | `[2601, 2602, 2603, 2604, 2605]` | `2.2` | `7.94` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_basic_stage_5` | `[2611, 2612, 2613, 2614]` | `2.84` | `10.21` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_mid_air_attack` | `[2615, 2616]` | `2.14` | `7.66` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_ground_heavy_hold` | `[2617, 2618, 2619, 2620, 2621, 2622, 2623]` | `2.94` | `6.58` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_graffiti_blast` | `[2624]` | `1.55` | `5.58` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_kaleidoscopic_mid_air_heavy` | `[2633, 2634, 2635, 2636, 2637, 2638, 2639]` | `5.81` | `13.02` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_resonance_skill_palette` | `[2662, 2663, 2664, 2665, 2666]` | `8.75` | `9.83` | `{"source_core_gain_1": 25.0, "overflow_gain": 25.0}` | `0` | `6.0` | source_confirmed |  |
| `lynae_resonance_skill_additive_color` | `[2672, 2673, 2674]` | `6.92` | `8.2` | `{}` | `0` | `6.0` | source_confirmed |  |
| `lynae_iridescent_splash` | `[2675, 2676, 2677, 2678]` | `8.13` | `7.65` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_visual_impact` | `[2679, 2680, 2681, 2682]` | `14.05` | `14.58` | `{}` | `0.0` | `25.0` | source_confirmed |  |
| `lynae_polychrome_leap_stage_1` | `[2641, 2642, 2643, 2644, 2645]` | `2.25` | `5.4` | `{"true_color_gain": 1.0, "lumiflow_cost": 40.0}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_polychrome_leap_stage_2` | `[2647, 2648, 2649, 2650, 2651]` | `0.38` | `0.9` | `{"true_color_gain": 1.0, "lumiflow_cost": 40.0}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_polychrome_leap_stage_3` | `[2653, 2654, 2660, 2661]` | `0.6` | `1.4` | `{"true_color_gain": 1.0, "lumiflow_cost": 40.0}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_intro_time_to_show_some_colors` | `[2689, 2690, 2691]` | `1.34` | `1.2` | `{"source_core_gain_1": 100.0, "overflow_gain": 100.0}` | `0` | `0.0` | source_confirmed |  |
| `lynae_resonance_liberation_prismatic_overblast` | `[2692, 2693, 2694, 2695]` | `0.0` | `20.0` | `{}` | `125` | `25` | source_confirmed |  |
| `lynae_to_a_vivid_tomorrow` | `[2696, 2697, 2698]` | `0.5` | `1.78` | `{}` | `0.0` | `0.0` | source_confirmed |  |
| `lynae_outro_lets_hit_the_road` | `[2699, 2700, 2701]` | `0.0` | `0.0` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_tune_break` | `[2702, 2703, 2704]` | `0.0` | `0.0` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_tune_response_spectral_analysis` | `[2735]` | `0.0` | `0.0` | `{}` | `0` | `0.0` | source_confirmed |  |
| `lynae_resonance_liberation` | `[]` | `0` | `0` | `{}` | `125` | `25` | non_damaging_selector |  |
| `lynae_resonance_liberation_prismatic_overblast_c5` | `[2692, 2693, 2694, 2695, 2483]` | `0.0` | `0.0` | `{}` | `125` | `25` | constellation_gated_disabled_by_default_workbook_confirmed_global_timestop_decision_frame_240F_damage_repeat_from_2695 |  |
