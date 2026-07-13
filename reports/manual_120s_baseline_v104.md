# Manual 120-Second Baseline Candidate 105

This is a deterministic human-authored 120.0 combat-second baseline for comparison. It is not a global optimum.

- Source baseline: 104 / ww-dps-simulator-2(104).zip
- Candidate status: pending external review
- Total damage: 5165134.682363359
- DPS: 43042.78901969466
- Final combat time: 120.0
- Final current/action time: 165.03333333333336
- Selected/resolved actions: 148 / 148
- Selected hash: `e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1`
- Resolved hash: `3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229`
- Damage by character: {"aemeath": 3733934.8538652016, "lynae": 1162391.9084385103, "mornye": 268807.92005964793}
- Placeholder swaps: 1 at [6]
- Tune Break times: [25.066666666666666, 54.93333333333333, 93.01666666666665]
- Final clipped action: {"damage_after_cutoff_excluded": 6395.257655214092, "damage_before_cutoff": 0.0, "effective_clipped_cost": 0.1666666666666714, "end_time": 120.0, "full_combat_time_cost": 0.6666666666666666, "resolved_action_id": "lynae_kaleidoscopic_basic_stage_3", "selected_action_id": "lynae_basic_attack", "start_time": 119.83333333333333, "step": 148, "truncated_by_combat_limit": true}

## Contribution

- aemeath: 3733934.8538652016 (72.2911%)
- lynae: 1162391.9084385103 (22.5046%)
- mornye: 268807.92005964793 (5.2043%)

## Action Counts

- aemeath_basic_attack: 22
- aemeath_echo_sigillum: 3
- aemeath_heavy_attack: 4
- aemeath_resonance_liberation: 3
- aemeath_resonance_skill: 29
- aemeath_tune_break: 3
- lynae_basic_attack: 6
- lynae_echo_hyvatia: 4
- lynae_polychrome_leap: 12
- lynae_resonance_liberation: 2
- lynae_resonance_skill: 5
- lynae_spark_collision: 4
- lynae_visual_impact: 4
- mornye_basic_attack: 20
- mornye_echo_reactor_husk: 4
- mornye_heavy_attack: 4
- mornye_resonance_liberation: 3
- mornye_resonance_skill: 5
- swap_to_aemeath: 3
- swap_to_lynae: 4
- swap_to_mornye: 4

## Resources

- Resonance Energy initial: {"aemeath": 125.0, "lynae": 125.0, "mornye": 175.0}
- Resonance Energy gained: {"aemeath": 173.71999999999997, "lynae": 247.90212000000002, "mornye": 360.5763839999999}
- Resonance Energy spent: {"aemeath": 249.99999999999997, "lynae": 250.0, "mornye": 525.0}
- Resonance Energy wasted: {"aemeath": 27.400000000000077, "lynae": 77.49212000000001, "mornye": 56.68230399999996}
- Resonance Energy final: {"aemeath": 48.71999999999999, "lynae": 122.90212000000002, "mornye": 10.576384000000001}
- Concerto initial: {"aemeath": 0.0, "lynae": 0.0, "mornye": 0.0}
- Concerto gained: {"aemeath": 300.00000000000006, "lynae": 388.5899999999999, "mornye": 336.0}
- Concerto spent: {"aemeath": 300.00000000000006, "lynae": 299.99999999999994, "mornye": 336.0}
- Concerto wasted: {"aemeath": 10.019999999999982, "lynae": 2.0, "mornye": 50.05000000000001}
- Concerto final: {"aemeath": 0.0, "lynae": 88.58999999999999, "mornye": 0.0}

## Damage Categories

- basic_attack: 1094364.097381991
- echo_ability: 77591.16254205018
- heavy_attack: 18666.068939718352
- intro: 80937.57188460515
- other: 0.0
- resonance_liberation: 2361954.741286322
- resonance_skill: 752161.9697089317
- tune_break: 779459.070619741
- Category sum: 5165134.682363359

## Active Echo Damage

- aemeath_echo_sigillum: {"activation_count": 3, "direct_damage": 0.0, "excluded_after_cutoff_damage": 0.0, "excluded_after_cutoff_hit_count": 0, "excluded_after_cutoff_resonance_energy": 0.0, "resolved_hit_count": 6, "scheduled_damage": 189947.5737285981, "total_damage": 189947.5737285981}
- lynae_echo_hyvatia: {"activation_count": 4, "direct_damage": 61574.7223428314, "excluded_after_cutoff_damage": 0.0, "excluded_after_cutoff_hit_count": 0, "excluded_after_cutoff_resonance_energy": 0.0, "resolved_hit_count": 40, "scheduled_damage": 0.0, "total_damage": 61574.7223428314}
- mornye_echo_reactor_husk: {"activation_count": 4, "direct_damage": 11093.654850417737, "excluded_after_cutoff_damage": 0.0, "excluded_after_cutoff_hit_count": 0, "excluded_after_cutoff_resonance_energy": 0.0, "resolved_hit_count": 4, "scheduled_damage": 0.0, "total_damage": 11093.654850417737}
- Total active Echo damage: 262615.95092184725

## Uptime

- Everbright Polestar liberation penetration uptime: 70.13333333333333
- Aemeath Trailblazing Star 5-set uptime: 70.11666666666665
- Mornye Halo of Starry Radiance 5-set uptime: 101.36666666666666

## Fields And Cutoff

- Mornye field event summary: {"event_count": 53, "first_time": 7.799999999999999, "last_time": 117.7}
- Lynae Spray Paint event summary: {"event_count": 10, "first_time": 20.883333333333336, "last_time": 118.91666666666666}
- Remaining scheduled effects at cutoff, not counted after 120: 2
- Final clipped action excluded damage: 6395.257655214092

## Known Limits

- Opening Aemeath -> Mornye normal swap still uses the known 0.50s placeholder.
- Mornye exact dodge-cancel next-input frame remains unresolved.
- Source-unconfirmed active-Echo Off-Tune values, including Lynae Hyvatia, remain unresolved.
- Final cutoff uses the existing runtime clip; post-120 scheduled effects remain uncounted.
