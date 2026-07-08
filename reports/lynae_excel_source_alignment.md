# Lynae Excel Source Alignment

Workbook: `data\source\鸣潮动作数据汇总.xlsx`
Source name: 琳奈

## Source Regions
- Damage coefficients: `dmg!2408:2490`
- Action/timing/resources: `角色-女!2577:2738`
- Skill type references: `角色技能类型!2553:2635`
- Base stat reference: `prop!51`
- Weapon reference only: `weapon!65`

## Implemented Action Map
- `lynae_basic_stage_1`: Basic Stage 1; action rows [2577]; damage rows [2408]; multiplier 0.8619; calculation single_damage_row; status implemented_v2
- `lynae_basic_stage_2`: Basic Stage 2; action rows [2578, 2579, 2580]; damage rows [2409, 2410, 2411]; multiplier 1.5717; calculation additive_hits; status implemented_v2
- `lynae_basic_stage_3`: Basic Stage 3; action rows [2581]; damage rows [2412]; multiplier 1.2337; calculation single_damage_row; status implemented_v2
- `lynae_dodge_counter`: Dodge Counter; action rows [2582]; damage rows [2413]; multiplier 2.3997; calculation single_damage_row; status implemented_v2
- `lynae_mid_air_attack`: Mid-air Attack; action rows [2583, 2584]; damage rows [2414, 2415]; multiplier 1.4365; calculation additive_hits; status implemented_v2
- `lynae_spark_collision_lv1`: Spark Collision Lv1; action rows [2586, 2587]; damage rows [2417, 2418]; multiplier 1.1112; calculation additive_hits; status implemented_v2
- `lynae_spark_collision_lv2`: Spark Collision Lv2; action rows [2588, 2589]; damage rows [2419, 2420]; multiplier 3.3334; calculation additive_hits; status implemented_v2
- `lynae_spark_collision_lv3`: Spark Collision Lv3; action rows [2590, 2591]; damage rows [2421, 2422]; multiplier 5.5556; calculation additive_hits; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_1`: KP Basic Stage 1; action rows [2592, 2593, 2594]; damage rows [2423]; multiplier 0.8281; calculation single_damage_row; status implemented_v2
- `lynae_kaleidoscopic_dodge_counter`: KP Dodge Counter; action rows [2595]; damage rows [2424]; multiplier 1.842; calculation single_damage_row; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_2`: KP Basic Stage 2; action rows [2596, 2597]; damage rows [2425, 2426]; multiplier 0.7774; calculation additive_hits; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_3`: KP Basic Stage 3; action rows [2598, 2599, 2600]; damage rows [2427, 2428, 2429]; multiplier 1.1325; calculation additive_hits; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_4`: KP Basic Stage 4; action rows [2601, 2602, 2603, 2604, 2605]; damage rows [2430, 2431, 2432, 2433]; multiplier 1.4874; calculation additive_hits; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_5`: KP Basic Stage 5; action rows [2611, 2612, 2613, 2614]; damage rows [2434, 2435, 2436]; multiplier 2.5181; calculation additive_hits_with_repeated_tick; status implemented_v2
- `lynae_kaleidoscopic_mid_air_attack`: KP Mid-air Attack; action rows [2615, 2616]; damage rows [2437, 2438]; multiplier 1.4365; calculation additive_hits; status implemented_v2
- `lynae_kaleidoscopic_ground_heavy_hold`: KP Ground Heavy Hold; action rows [2617, 2618, 2619, 2620, 2621, 2622, 2623]; damage rows [2439, 2440, 2441, 2442, 2443, 2444, 2445]; multiplier 1.2341; calculation additive_hits; status implemented_v2_timing_simplified
- `lynae_kaleidoscopic_graffiti_blast`: KP Graffiti Blast; action rows [2624]; damage rows [2446]; multiplier 1.0478; calculation single_damage_row; status implemented_v2
- `lynae_kaleidoscopic_mid_air_heavy`: KP Mid-air Heavy; action rows [2633, 2634, 2635, 2636, 2637, 2638, 2639]; damage rows [2447, 2448, 2449, 2450, 2451, 2452, 2453]; multiplier 2.4339; calculation additive_hits; status implemented_v2_timing_simplified
- `lynae_resonance_skill_palette`: Lynae-Style Palettes; action rows [2662, 2663, 2664, 2665, 2666]; damage rows [2454, 2455, 2456, 2457]; multiplier 2.7863; calculation additive_hits; status implemented_v2
- `lynae_resonance_skill_additive_color`: Additive Color; action rows [2672, 2673, 2674]; damage rows [2458, 2459]; multiplier 2.3262; calculation additive_hits; status implemented_v2
- `lynae_iridescent_splash`: Iridescent Splash C0; action rows [2675, 2676, 2677, 2678]; damage rows [2460, 2461]; multiplier 3.0418; calculation mutually_exclusive_mode_variants_same_multiplier; status implemented_v2
- `lynae_visual_impact`: Visual Impact C0; action rows [2679, 2680, 2681, 2682]; damage rows [2464, 2465]; multiplier 12.1672; calculation mutually_exclusive_mode_variants_same_multiplier; status implemented_v2_periodic_spray_metadata_only
- `lynae_polychrome_leap_stage_1`: Polychrome Leap Stage 1 C0; action rows [2641, 2642, 2643, 2644, 2645]; damage rows [2468, 2469, 2470]; multiplier 1.014; calculation additive_hits; status implemented_v2
- `lynae_polychrome_leap_stage_2`: Polychrome Leap Stage 2 C0; action rows [2647, 2648, 2649, 2650, 2651]; damage rows [2474]; multiplier 1.014; calculation repeated_tick_mode_variants_same_multiplier; status implemented_v2
- `lynae_polychrome_leap_stage_3`: Polychrome Leap Stage 3 C0; action rows [2653, 2654, 2660, 2661]; damage rows [2476, 2477]; multiplier 0.655; calculation additive_hits_with_repeated_tick; status implemented_v2
- `lynae_intro_time_to_show_some_colors`: Intro Skill; action rows [2689, 2690, 2691]; damage rows [2480, 2481]; multiplier 2.248; calculation repeated_tick_mutually_exclusive_mode_variants_same_multiplier; status implemented_v2
- `lynae_resonance_liberation_prismatic_overblast`: Prismatic Overblast C0; action rows [2692, 2693, 2694, 2695]; damage rows [2482]; multiplier 8.748; calculation repeated_tick; status implemented_v2
- `lynae_to_a_vivid_tomorrow`: To a Vivid Tomorrow; action rows [2696, 2697, 2698]; damage rows [2484, 2485]; multiplier 2.0106; calculation additive_repeated_ticks; status implemented_v2
- `lynae_outro_lets_hit_the_road`: Outro; action rows [2699, 2700, 2701]; damage rows [2486, 2487]; multiplier 1.0; calculation excel_tick_sum_and_tooltip_confirmed; status implemented_v2_tooltip_damage
- `lynae_tune_break`: Tune Break; action rows [2702, 2703, 2704]; damage rows [2488]; multiplier 0.0; calculation tune_break_rate_lv_1_formula; status excel_tune_break_single_target_v1
- `lynae_tune_response_spectral_analysis`: Spectral Analysis C0; action rows [2735]; damage rows [2489]; multiplier 18.8075; calculation tune_response_executable_source; status implemented_v2

## Tune Break Damage Formula
- `lynae_tune_break`: dmg!2488 RateLv1 `160000` is implemented as Tune Break multiplier `16.0`.
- `lynae_tune_break`: dmg!2488 RateLv10 is not used as a normal damage source.
- `lynae_tune_break`: implemented through the Tune Break damage formula, not normal Spectro ATK damage.
- `lynae_tune_break`: 角色-女2703 confirms global time stop.
- `lynae_tune_break`: 角色-女2704 gives hit frame `72F` and action window `96F`.

## Additive Hit Rows
- `lynae_basic_stage_2`: dmg!2409, dmg!2410, dmg!2411 are additive hits.
- `lynae_mid_air_attack`: dmg!2414, dmg!2415 are additive hits.
- `lynae_spark_collision_lv1`: dmg!2417, dmg!2418 are additive hits.
- `lynae_spark_collision_lv2`: dmg!2419, dmg!2420 are additive hits.
- `lynae_spark_collision_lv3`: dmg!2421, dmg!2422 are additive hits.
- `lynae_kaleidoscopic_basic_stage_2`: dmg!2425, dmg!2426 are additive hits.
- `lynae_kaleidoscopic_basic_stage_3`: dmg!2427, dmg!2428, dmg!2429 are additive hits.
- `lynae_kaleidoscopic_basic_stage_4`: dmg!2430, dmg!2431, dmg!2432, dmg!2433 are additive hits.
- `lynae_kaleidoscopic_ground_heavy_hold`: dmg!2439, dmg!2440, dmg!2441, dmg!2442, dmg!2443, dmg!2444, dmg!2445 are additive hits.
- `lynae_kaleidoscopic_mid_air_heavy`: dmg!2447, dmg!2448, dmg!2449, dmg!2450, dmg!2451, dmg!2452, dmg!2453 are additive hits.
- `lynae_resonance_skill_palette`: dmg!2454, dmg!2455, dmg!2456, dmg!2457 are additive hits.
- `lynae_resonance_skill_additive_color`: dmg!2458, dmg!2459 are additive hits.
- `lynae_polychrome_leap_stage_1`: dmg!2468, dmg!2469, dmg!2470 are additive hits.

## Repeated-Hit / Tick Rows
- `lynae_kaleidoscopic_basic_stage_5`: dmg!2435 repeats max 5 from 角色-女!2613.
- `lynae_polychrome_leap_stage_2`: dmg!2474 repeats max 6 from 角色-女!2649, 角色-女!2650.
- `lynae_polychrome_leap_stage_3`: dmg!2476 repeats max 4 from 角色-女!2660.
- `lynae_intro_time_to_show_some_colors`: dmg!2480, dmg!2481 repeats max 10 from 角色-女!2689.
- `lynae_resonance_liberation_prismatic_overblast`: dmg!2482 repeats max 10 from 角色-女!2695.
- `lynae_to_a_vivid_tomorrow`: dmg!2484 repeats max 12 from 角色-女!2697.
- `lynae_to_a_vivid_tomorrow`: dmg!2485 repeats max 10 from 角色-女!2698.
- `lynae_outro_lets_hit_the_road`: dmg!2486 repeats max 12 from 角色-女!2700.
- `lynae_outro_lets_hit_the_road`: dmg!2487 repeats max 10 from 角色-女!2701.

## Mutually Exclusive Mode Variants
- `lynae_iridescent_splash`: dmg!2460, dmg!2461 are mode variants and are not additive.
- `lynae_visual_impact`: dmg!2464, dmg!2465 are mode variants and are not additive.
- `lynae_intro_time_to_show_some_colors`: dmg!2480, dmg!2481 are mode variants and are not additive.

## Constellation-Gated Disabled By Default
- `lynae_iridescent_splash_c3`: multiplier 5.7795; rows dmg!2462, dmg!2463; disabled by default.
- `lynae_visual_impact_c3`: multiplier 23.1177; rows dmg!2466, dmg!2467; disabled by default.
- `lynae_polychrome_leap_stage_1_c1`: multiplier 2.2308; rows dmg!2471:2473; disabled by default.
- `lynae_polychrome_leap_stage_2_c1`: multiplier 2.2308; rows dmg!2475; disabled by default.
- `lynae_polychrome_leap_stage_3_c1`: multiplier 1.441; rows dmg!2478:2479; disabled by default.
- `lynae_resonance_liberation_prismatic_overblast_c5`: multiplier 14.871; rows dmg!2483; disabled by default.
- `lynae_tune_response_spectral_analysis_c2`: multiplier 31.9727; rows dmg!2490; disabled by default.

## Implemented Single-Target Mechanics
- tune_strain_stack_limit_and_per_stack_damage: implemented_single_target (角色-女!2728) - Current single-target Endgame Matrix model increments Tune Strain Interfered stacks on Tune Break, caps at 1 stack for C0 and 2 stacks for C2+, lasts 30s, and applies only to Lynae damage. This is not a multi-target implementation claim.

## Unresolved / Metadata-Only Rows
- continuous_lumiflow_movement_recovery: user_tooltip_confirmed_timing_simplified (角色-女!2709) - Simulator is action-step based and has no continuous movement/skating state.
- spray_paint_periodic_ticks: metadata_only_window_recorded (角色-女!2683:2688) - Visual Impact records the 5s window and immediate Flux; periodic 2s field scheduling is not added.
- constellation_variants: constellation_gated_disabled_by_default (dmg!2462:2463, dmg!2466:2467, dmg!2471:2473, dmg!2475, dmg!2478:2479, dmg!2483, dmg!2490) - Non-S0 variants are retained as source-aligned records but not selected by default.
- skill_type_reference_region: workbook_reference_corrected (角色技能类型!2553:2635) - Rows 772:784 are not the Lynae skill type region and are no longer used for Lynae.
