# Lynae Excel Source Alignment

Workbook: `data\source\鸣潮动作数据汇总.xlsx`
Source name: 琳奈

## Implemented Action Map
- `lynae_basic_stage_1`: Basic Stage 1; action rows [2577]; damage rows [2408]; multiplier 0.8619; status implemented_v2
- `lynae_basic_stage_2`: Basic Stage 2; action rows [2578, 2579, 2580]; damage rows [2409, 2410, 2411]; multiplier 1.5717; status implemented_v2
- `lynae_basic_stage_3`: Basic Stage 3; action rows [2581]; damage rows [2412]; multiplier 1.2337; status implemented_v2
- `lynae_dodge_counter`: Dodge Counter; action rows [2582]; damage rows [2413]; multiplier 2.3997; status implemented_v2
- `lynae_mid_air_attack`: Mid-air Attack; action rows [2583, 2584]; damage rows [2414, 2415]; multiplier 1.4365; status implemented_v2
- `lynae_spark_collision_lv1`: Spark Collision Lv1; action rows [2586, 2587]; damage rows [2417, 2418]; multiplier 1.1112; status implemented_v2
- `lynae_spark_collision_lv2`: Spark Collision Lv2; action rows [2588, 2589]; damage rows [2419, 2420]; multiplier 3.3334; status implemented_v2
- `lynae_spark_collision_lv3`: Spark Collision Lv3; action rows [2590, 2591]; damage rows [2421, 2422]; multiplier 5.5556; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_1`: KP Basic Stage 1; action rows [2592, 2593, 2594]; damage rows [2423]; multiplier 0.8281; status implemented_v2
- `lynae_kaleidoscopic_dodge_counter`: KP Dodge Counter; action rows [2595]; damage rows [2424]; multiplier 1.842; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_2`: KP Basic Stage 2; action rows [2596, 2597]; damage rows [2425, 2426]; multiplier 0.7774; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_3`: KP Basic Stage 3; action rows [2598, 2599, 2600]; damage rows [2427, 2428, 2429]; multiplier 1.1325; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_4`: KP Basic Stage 4; action rows [2601, 2602, 2603, 2604, 2605]; damage rows [2430, 2431, 2432, 2433]; multiplier 1.4874; status implemented_v2
- `lynae_kaleidoscopic_basic_stage_5`: KP Basic Stage 5; action rows [2611, 2612, 2613, 2614]; damage rows [2434, 2435, 2436]; multiplier 1.9137; status implemented_v2
- `lynae_kaleidoscopic_mid_air_attack`: KP Mid-air Attack; action rows [2615, 2616]; damage rows [2437, 2438]; multiplier 1.4365; status implemented_v2
- `lynae_kaleidoscopic_ground_heavy_hold`: KP Ground Heavy Hold; action rows [2617, 2618, 2619, 2620, 2621, 2622, 2623]; damage rows [2439, 2440, 2441, 2442, 2443, 2444, 2445]; multiplier 1.2341; status implemented_v2_timing_simplified
- `lynae_kaleidoscopic_graffiti_blast`: KP Graffiti Blast; action rows [2624]; damage rows [2446]; multiplier 1.0478; status implemented_v2
- `lynae_kaleidoscopic_mid_air_heavy`: KP Mid-air Heavy; action rows [2633, 2634, 2635, 2636, 2637, 2638, 2639]; damage rows [2447, 2448, 2449, 2450, 2451, 2452, 2453]; multiplier 2.4339; status implemented_v2_timing_simplified
- `lynae_resonance_skill_palette`: Lynae-Style Palettes; action rows [2662, 2663, 2664, 2665, 2666]; damage rows [2454, 2455, 2456, 2457]; multiplier 2.7863; status implemented_v2
- `lynae_resonance_skill_additive_color`: Additive Color; action rows [2672, 2673, 2674]; damage rows [2458, 2459]; multiplier 2.3262; status implemented_v2
- `lynae_iridescent_splash`: Iridescent Splash C0; action rows [2675, 2676, 2677, 2678]; damage rows [2460, 2461]; multiplier 6.0836; status implemented_v2
- `lynae_visual_impact`: Visual Impact C0; action rows [2679, 2680, 2681, 2682]; damage rows [2464, 2465]; multiplier 24.3344; status implemented_v2_periodic_spray_metadata_only
- `lynae_polychrome_leap_stage_1`: Polychrome Leap Stage 1 C0; action rows [2641, 2642, 2643, 2644, 2645]; damage rows [2468, 2469, 2470]; multiplier 1.014; status implemented_v2
- `lynae_polychrome_leap_stage_2`: Polychrome Leap Stage 2 C0; action rows [2647, 2648, 2649, 2650, 2651]; damage rows [2474]; multiplier 0.169; status implemented_v2
- `lynae_polychrome_leap_stage_3`: Polychrome Leap Stage 3 C0; action rows [2653, 2654, 2660, 2661]; damage rows [2476, 2477]; multiplier 0.262; status implemented_v2
- `lynae_intro_time_to_show_some_colors`: Intro Skill; action rows [2689, 2690, 2691]; damage rows [2480, 2481]; multiplier 0.4496; status implemented_v2
- `lynae_resonance_liberation_prismatic_overblast`: Prismatic Overblast C0; action rows [2692, 2693, 2694, 2695]; damage rows [2482]; multiplier 0.8748; status implemented_v2
- `lynae_to_a_vivid_tomorrow`: To a Vivid Tomorrow; action rows [2696, 2697, 2698]; damage rows [2484, 2485]; multiplier 0.1843; status implemented_v2
- `lynae_outro_lets_hit_the_road`: Outro; action rows [2699, 2700, 2701]; damage rows [2486, 2487]; multiplier 0.0; status implemented_v2_tooltip_damage
- `lynae_tune_break`: Tune Break; action rows [2702, 2703, 2704]; damage rows [2488]; multiplier 0.0; status metadata_only_zero_workbook_damage
- `lynae_tune_response_spectral_analysis`: Spectral Analysis C0; action rows [2735]; damage rows [2489]; multiplier 18.8075; status implemented_v2

## Unresolved / Metadata-Only Rows
- continuous_lumiflow_movement_recovery: user_tooltip_confirmed_timing_simplified (角色-女!2709) - Simulator is action-step based and has no continuous movement/skating state.
- spray_paint_periodic_ticks: metadata_only_window_recorded (角色-女!2683:2688) - Visual Impact records the 5s window and immediate Flux; periodic 2s field scheduling is not added.
- tune_strain_stack_limit_and_per_stack_damage: metadata_only_no_stack_system_hook (角色-女!2728) - Current simulator has interfered state and responses but no target Tune Strain stack model.
- constellation_variants: constellation_gated_disabled_by_default (dmg!2462:2463, dmg!2466:2467, dmg!2471:2473, dmg!2475, dmg!2478:2479, dmg!2483, dmg!2490) - Non-S0 variants are retained as source-aligned records but not selected by default.
