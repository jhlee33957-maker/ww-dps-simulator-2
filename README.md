# Wuwa DPS RL Simulator Prototype

This project is a Wuthering Waves-style DPS simulation tool focused on Maskable PPO reinforcement learning. It combines a deterministic simulator core, a Gymnasium environment with action masks, reusable damage formulas, training and evaluation scripts, and a Streamlit UI for deterministic validation and saved-model evaluation. It is still a prototype and uses dummy data rather than real game values.

## Current Scope

- Deterministic 120-second combat simulation.
- Time advances by action duration, not by fixed frames or ticks.
- The player or agent chooses a new action only after the current action finishes.
- If an action starts before 120.0 seconds and crosses the limit, combat-time effects and damage are clipped at the configured combat duration.
- Final DPS is always total_damage / 120.0.
- Gymnasium environment for Maskable PPO training.
- Streamlit UI with Demo Sequence, PPO Model evaluation, and Character Mechanics reference modes.
- Dummy character, action, enemy, and buff data are included. No real game data is used.

## Character Mechanics Architecture

The common combat engine handles shared systems: damage formulas, action_time, hit timing, buffs, cooldowns, resources, attribute anomaly state, Havoc Bane DEF reduction, and the PPO reward objective. Character-specific mechanics are isolated under characters/ so the simulator core does not need character-specific branches.

## Energy Regen

Characters now support `energy_regen` as a decimal stat where `1.0 = 100%` and missing values default to `1.0`. The stat applies only to Resonance Energy gain: `final_resonance_energy_gain = base_resonance_energy_gain * actor.energy_regen`. Resonance Energy costs, Concerto gain, Mornye Rest Mass Energy, Mornye Relative Momentum, cooldowns, and direct damage are not scaled by this shared resource formula. Timeline rows log base Resonance Energy gain, Energy Regen, final Resonance Energy gain, gained energy after caps, and wasted energy.

Character mechanic modules can:

- initialize character-specific state
- resolve high-level actions into concrete actions
- add character-specific action availability rules
- advance character-specific timers whenever combat time passes
- update state before and after actions
- extend PPO observations
- provide debug state for Streamlit and smoke tests

Existing dummy characters use DefaultCharacterMechanic, which is a no-op. AemeathMechanic contains the first Aemeath-lite implementation. It resolves high-level policy actions into concrete internal actions and owns Aemeath-specific state updates. Full real-game Aemeath logic is planned later.

## Party Simulation Foundation v1

The simulator now has a party-state foundation with `party_members`, `active_character_id`, per-character `character_states`, team buffs, enemy state, combat/action clocks, cooldowns, action logs, and damage logs. The existing `CombatState` remains the execution state for backward compatibility, and `Simulation.party_state` exposes the party-oriented view.

Three party presets are included in `data/party_presets.json`:

- `aemeath`: Aemeath Solo, preserving the existing solo Aemeath behavior.
- `aemeath_test_party`: Aemeath, Dummy Support, and Dummy Sub DPS for structural party testing.
- `aemeath_mornye_test_party`: Mornye, Aemeath, and Dummy Sub DPS for real-support party testing.

## Aemeath + Mornye Party Defaults

Aemeath supports both `fusion_burst` and `tune_rupture` resonance modes. For Aemeath + Mornye party presets, the intended default is `aemeath_resonance_mode = "tune_rupture"`; Fusion Burst remains available for other party compositions and for explicit manual/CLI overrides.

Mornye uses `mornye_heal_event_mode = "simplified_syntony_field_uptime"` by default in Aemeath + Mornye party presets for practical DPS evaluation. This treats Syntony Field uptime as maintaining the `team_heal` proxy, so Halo of Starry Radiance 5-set ATK buff is expected to remain active while Syntony Field uptime is maintained. PPO training/evaluation should use these party defaults unless intentionally comparing another mode.

Generic swap actions are available for non-active party members. Party swaps are now treated as transition requests, not authoritative gameplay timing. `data/transition_config.json` and optional preset `generic_swap` metadata provide the current `0.50s` placeholder fallback; this intentionally overrides legacy `swap_to_*` action timings such as old `0.30s` dummy swaps. Timeline rows include transition metadata such as outgoing/incoming character IDs, transition events, placeholder timing source, fallback usage, and Intro/Outro event IDs.

The generic team buff foundation supports target scopes, optional tag filters, stat modifiers, and damage amp modifiers. `dummy_support` and `dummy_sub_dps` are test-only characters, not real Wuthering Waves data. `dummy_support_buff` applies a party damage amp buff for testing swap and buff persistence, while `dummy_support` also has a zero-time test-only outgoing Outro-like event that applies `dummy_support_outro_damage_amp` through the transition config. Mornye is the first real support character and applies `mornye_outro_recursion_all_dmg_amp` through her implemented Outro transition. Aemeath QTE/Intro/Outro rows are extracted section-locally for review only, ignoring QTE rows from other character sections, and remain disabled/non-executable. Raw Aemeath QTE rows are split into action-ready review candidates named `aemeath_qte_intro_human` and `aemeath_qte_intro_mech` when both workbook sections are present; they are proposed future transition actions, not executable simulator actions. Full real Intro/Outro/QTE timing, Starflux, Tune/Fusion/Trail systems, and real party rotations remain out of scope.

No PPO retraining was performed for this foundation patch. Saved PPO models are party/action-space specific and should be retrained before use with new party presets.

## Excel-based Tune Break System

The Aemeath + Mornye party preset can use a single-target Excel-based Off-Tune / Mistune / Tune Break system. Normal sourced actions add `off_tune_value * current_off_tune_buildup_rate` to the enemy gauge, using `3920` as the current boss-style default cap. While Tune Break cooldown is active, Off-Tune accumulation is blocked entirely. When the gauge reaches cap outside cooldown, Mistune makes character-specific Tune Break actions available; Tune Break is not automatic damage and is not forced into a rotation.

Aemeath Tune Break uses coefficients `1.0` and `12.0`; Mornye Tune Break uses `1.7334`, `2.2666`, and `12.0`. Tune Break damage uses fixed base `10000 * multiplier * boost * RES * DEF * Tune DMG Bonus` and does not use ATK/DEF/HP scaling or normal damage bonus categories.

After the final Tune Break hit, sourced Shifting/Offset state can become Interfered. The same hit removes Mistune/offset state, resets the Off-Tune gauge to `0`, and starts a `3.0s` boss Tune Break cooldown sourced from workbook `附页2!B227` for COST4/red-name targets. Mornye Observation Marker plus Tune Break applies Interfered Marker as target damage taken amplification. For the real-test Mornye profile with Energy Regen `2.7944`, the amp reaches the `40%` cap. Aemeath Starburst and Mornye Particle Jet response scans are logged with 8s same-target cooldowns; unresolved response damage is intentionally not invented.

Off-Tune values are mapped from workbook `角色-女` column `S`; the current mapping audit is in `reports/off_tune_value_mapping_audit.md` and `data/extracted/off_tune_value_mapping_audit.json`. Notable corrections include `mornye_heavy_geopotential_shift = 29.6` from `角色-女!S4117` and `mornye_heavy_inversion = 104.0` from `角色-女!S4136`. Transition QTE/Intro actions preserve Off-Tune source metadata when converted to runtime actions.

The legacy `simplified_on_inversion` Interfered approximation is still available only when explicitly configured. PPO models should be retrained after this patch because action availability, simulator state, and damage/debuff behavior changed. No PPO training was performed for this patch.

## Concerto-Gated Transition v1

Each party member now has per-character `concerto_energy`, `concerto_energy_cap`, and `concerto_ready` fields exposed through `party_state.character_states`. Normal character actions add their configured `concerto_energy_gain` and clamp to the cap. Swap requests do not invent concerto gain.

No-concerto swaps use the generic fallback transition, log `transition_type = normal_swap` and `transition_reason = concerto_not_ready`, change the active character, and skip outgoing Outro plus incoming QTE/Intro. Full-concerto swaps log `transition_type = full_concerto_transition` and become eligible for configured transition hooks. The generic fallback swap timing remains a placeholder and should not be interpreted as real game data.

Aemeath QTE candidates exist in `data/extracted/aemeath_qte_action_candidates.json` and reviewed executable transition actions exist in `data/transition_actions.json`, but QTE is disabled by default and is not a policy action. QTE modes are configured in `data/transition_config.json`: `disabled` logs candidate availability without applying QTE; `dry_run` logs candidate timing, multipliers, classification, and previous-Outro metadata without DPS effects; `enabled` applies reviewed transition action damage/time through the generic transition-action pipeline. Flow Light, E1-QTE follow-up, and real previous-Outro trigger timing are not applied in v1.

The unsupported observation that a no-concerto swap into Aemeath uses Basic Stage 2 is not implemented due to insufficient source support. Aemeath solo behavior is unchanged.

## Aemeath QTE Enabled Transition v1

QTE is triggered only by a party swap transition when the outgoing character has full Concerto and `qte_mode == enabled`. It remains hidden from PPO and is never directly selectable; `swap_to_aemeath` is still the selected policy action, while the resolved internal action is `transition:aemeath_qte_intro_human` or `transition:aemeath_qte_intro_mech`.

The enabled path is data-driven through `data/transition_actions.json` and `simulator/transition_actions.py`, so future characters can reuse the same transition action schema. Human Aemeath QTE uses `action_time = 1.0`, `combat_time_cost = 0.1667`, and `damage_bonus_category = none_or_unmodeled_intro`. Mech Aemeath QTE uses `action_time = 1.2`, `combat_time_cost = 0.4333`, and `damage_bonus_category = resonance_skill`. Transition actions preserve raw Excel metadata in UTF-8/Unicode-safe form for auditability: Human QTE raw category is `变奏 / 变奏伤害`, while Mech QTE raw category is `共鸣技能 / 变奏伤害`. Functional simulation uses `trigger_classification`, `source_damage_label`, and `damage_bonus_category`.

Default `qte_mode` remains `disabled`. `dry_run` logs the selected transition action only. `enabled` applies reviewed candidate damage/time, consumes outgoing Concerto when configured, and logs trigger classification, source damage label, previous-Outro trigger frame, and Flow Light metadata. Flow Light / `流光增幅状态` and E1-QTE follow-up are not implemented yet. No-concerto swaps remain fallback only, and the unsupported A2 normal swap-in observation is not implemented.

## Mornye Support v1

Mornye is added as the first real support character module under `characters/mornye.py` and is registered through the generic character registry. She is party-capable, non-dummy, Fusion-aligned, and available in `aemeath_mornye_test_party` with Aemeath and Dummy Sub DPS. The Streamlit Character Mechanics page includes `data/mechanics/mornye_mechanics.json`.

Mornye v1 uses the source workbook section `莫宁`: frame sheet `角色-女` rows 4102-4185 and skill/type sheet `角色技能类型` rows 2639-2673. Coefficients use the workbook values that match the provided screenshot sanity checks, including Basic, Wide Field Observation Basic, Heavy, Skill, Liberation, Syntony Field, and Intro Convergence multipliers. Action timing uses clear action-end frame values divided by 60 where available; transition Outro timing is zero-time and generic swap timing still supplies the swap cost.

Implemented in v1:

- baseline / Wide Field Observation mode
- Rest Mass Energy and Relative Momentum, each capped at 100
- baseline Basic and WFO Basic action resolution skeletons
- Heavy Geopotential Shift at 100 Rest Mass, entering WFO for 30s and generating Syntony Field for 25s
- Heavy Inversion at 100 Relative Momentum, applying Observation Marker metadata for 30s
- Expectation Error / Optimal Solution Resonance Skill routing: baseline resolves conservatively to Expectation Error by default; WFO resolves to Distributed Array
- Critical Protocol Resonance Liberation, including Syntony Field to High Syntony Field conversion
- High Syntony Field simplified runtime support: 25s duration, party DEF +20%, inherited Off-Tune +50%, inherited simplified healing proxy, and Critical Protocol same-action support application
- Mornye Energy Regen scaling v1: Mornye uses `energy_regen = 2.60` as a configurable support-test assumption, and Critical Protocol gets temporary ER-derived crit bonuses only on that Liberation action
- optional simplified Interfered Marker mode: when explicitly enabled, Heavy Inversion refreshes a 30s enemy damage-taken amp based on Mornye ER excess; global default remains disabled
- Mornye Outro Recursion as a real transition buff: `mornye_outro_recursion_all_dmg_amp` gives the party 25% All DMG Amplification for 30s and consumes Mornye outgoing Concerto when applied

Not implemented in v1:

- full Tune Break / Tune Rupture / Tune Strain systems
- full Interfered Marker Tune conversion and Particle Jet response
- full GP/counter timing against enemy attacks for automatic Optimal Solution success
- Proof of Boundedness defensive survival logic
- exact healing / DEF defensive value in DPS
- automatic Syntony Field damage scheduling
- full QTE/Intro state-machine details beyond reviewed transition data

Mornye Intro Convergence is present as reviewed transition data in `data/transition_actions.json` and remains disabled by default through `data/transition_config.json`. It is transition-only, not a policy action. No PPO retraining was performed.

## Mornye Expectation Error / Optimal Solution

Mornye Resonance Skill no longer automatically resolves to Optimal Solution in baseline mode. The policy action remains `mornye_resonance_skill`, but conservative baseline routing now resolves to `mornye_skill_expectation_error`. Optimal Solution is treated as the GP/counter success follow-up rather than a normal always-available Resonance Skill result.

The configurable `mornye_expectation_error_mode` lives under Mornye mechanics config. The default is `expectation_error_only`, which applies Expectation Error and logs `gp_success_not_modeled` without Optimal Solution damage or Rest Mass effects. `dry_run_success_candidate` also resolves to Expectation Error but logs `mornye_skill_optimal_solution` as the success candidate. `always_success` is an optimistic diagnostic mode only; it forces simplified GP success and preserves the old direct Optimal Solution behavior only when explicitly enabled.

Full enemy attack timing and GP/counter success detection are not implemented. The `aemeath_mornye_enabled_test_party` preset stays conservative for this routing; `aemeath_mornye_optimistic_gp_test_party` is the explicit optimistic preset. PPO models trained before this routing fix are stale for Mornye party evaluation and should not be reused without retraining. No PPO training was performed for this patch.

## Mornye ER Scaling v1

Mornye helper formulas live in `characters/mornye.py`. ER excess percent is `max(0, (energy_regen - 1.0) * 100)`. Interfered Marker amp potential is `min(excess_percent * 0.0025, 0.40)`, so 100% ER gives 0%, 160% ER gives 15%, and 260% ER caps at 40%. Critical Protocol temporary crit bonuses are `min(excess_percent * 0.005, 0.80)` crit rate and `min(excess_percent * 0.01, 1.60)` crit damage; at 260% ER this is +80% CR and +160% CD.

`data/transition_config.json` keeps Mornye ER scaling enabled and Interfered Marker mode disabled by default. The supported marker modes are `disabled`, `dry_run`, and `simplified_on_inversion`. The `aemeath_mornye_enabled_test_party` preset opts into `simplified_on_inversion` for deterministic support-testing because that preset already enables experimental transition behavior. Full Tune/Tune Rupture/Tune Strain marker conversion, Proof of Boundedness, healing, and DEF survival value remain out of scope.

## Mornye Off-Tune Buildup Rate and Halo of Starry Radiance Echo Set

Off-Tune Buildup Rate is modeled as an explicit support stat, `support_stats.off_tune_buildup_rate`. The default is 100% = `1.0` for every character when a profile does not provide a value. Energy Regen is separate and is never used as Off-Tune Buildup Rate.

Mornye Syntony Field grants party Off-Tune Buildup Rate +50% from workbook row `角色-女!D4122`. C2 can add another +20%, but the default `mornye_constellation` is `0`, so that bonus is disabled unless config sets `mornye_constellation >= 2`.

Halo of Starry Radiance 5-set is implemented for Mornye user profile `mornye_user_real_01`:

- Trigger: `team_heal` event.
- Current `team_heal` support: simplified Syntony Field healing proxy.
- Exact healing amount and exact 180F / 3s tick timing are not modeled.
- Formula: `ATK% = min(current_off_tune_buildup_rate * 0.20, 0.25)`.
- Base `1.0` -> ATK +20%.
- Syntony Field `1.5` -> ATK +25% cap.
- Duration: 4s.
- Max stacks: 1.
- Retrigger behavior: refresh duration and recalculate value.

Field-creating Mornye actions receive the Halo 5-set buff on their own damage in the current action-level approximation, `same_action_field_creation_approximation`. The Syntony Field Off-Tune +0.5 support-stat buff is applied before calculating the same-action Halo value.

The Halo 5-set buff is team ATK%, so it benefits ATK-scaling party members such as Aemeath. It does not increase Mornye DEF-scaling damage. The 2-set Healing Bonus is metadata only for current DPS. Full healing amount calculation, exact heal tick scheduling, defensive survival value, and full automatic Syntony/High Syntony Field damage scheduling remain unsupported.

PPO should be retrained only after Mornye `mornye_heal_event_mode` / field proxy behavior is finalized. No PPO training was performed for this patch.

## Mornye High Syntony Field / Critical Protocol

Critical Protocol can generate High Syntony Field when Syntony Field is active. The runtime model consumes/replaces Syntony Field, creates High Syntony Field for 25s, and applies party DEF +20% as a real runtime `def_percent` buff.

High Syntony Field inherits Syntony Field's Off-Tune +50% and the simplified healing proxy. The inherited healing multiplier +40% is metadata only because exact healing amount and exact heal tick timing are not modeled. Halo of Starry Radiance 5-set can remain active through the High Syntony heal proxy, but Halo ATK% does not increase Mornye DEF-scaling damage.

Critical Protocol receives High Syntony Field DEF +20% under `same_action_high_syntony_field_creation_approximation` when active Syntony Field exists before casting. Automatic Syntony/High Syntony field damage scheduling, full Tune Break / Interfered systems, and exact healing remain unsupported. PPO should be retrained after this correction because Mornye Liberation's support value changed; no PPO training was performed for this patch.

## Mornye Excel Audit

The read-only Mornye Excel audit compares the current Mornye v1 implementation against the workbook section for source character `莫宁`. Run it with:

```bash
python scripts/extract_mornye_excel_audit.py
python scripts/mornye_excel_audit_smoke_test.py
```

Generated review artifacts:

- `data/extracted/mornye_excel_audit.json`
- `data/extracted/mornye_source_alignment_candidates.json`
- `data/extracted/mornye_unresolved_rows.json`
- `reports/mornye_excel_audit.md`
- `reports/mornye_source_alignment_review.md`

The audit is intentionally report-only. It does not modify `data/actions.json`, change Mornye gameplay behavior, enable Intro/QTE behavior, train PPO, or implement future Tune/Interfered/Proof/healing/DEF systems. The smoke test hashes `data/actions.json` before and after extraction to guard that contract.

## Mornye Excel Source Audit

Mornye mechanics are under source audit. Existing simulator behavior may be incomplete, especially around Interfered Marker, Tune/Tune Rupture-like systems, Syntony Field scheduling, QTE Concerto, and route timing. Do not treat current Mornye cycle timing as final until audit-based patches are reviewed and applied.

The source-evidence audit outputs are written under `reports/` and `data/extracted/` with workbook sheet, row, column, and raw cell evidence. Claims that cannot be proven from the workbook are marked unresolved/source_partial/source_conflict rather than implemented.

Run:

```bash
python scripts/extract_mornye_excel_source_audit.py
python scripts/mornye_excel_source_audit_smoke_test.py
```

The audit is report-only and must not change simulator mechanics, party presets, damage formulas, action timings, resource values, or PPO reward logic.

## Mornye Action Data Timing / Resource Corrections

The source guard `scripts/mornye_action_data_source_guard_smoke_test.py` checks the workbook `data/source/鸣潮动作数据汇总.xlsx`, sheet `角色-女`, around rows 4102-4164. It writes source evidence to `data/extracted/mornye_action_data_time_resource_source_guard.json` and `reports/mornye_action_data_time_resource_source_guard.md`.

Timing now distinguishes plain source `时停` from source `全局时停`:

- `action_time` is animation/action lock duration.
- `combat_time_cost` is timed-combat timer loss.
- Only `AC = 全局时停` reduces combat timer loss.
- `AC = 时停` alone is logged as non-global time stop and does not reduce `combat_time_cost`.

Source-confirmed corrections:

- Critical Protocol Liberation uses rows 4150, 4151, 4153, and 4154. `action_time` remains `296F / 60 = 4.9333`, but `combat_time_cost = 0.0` because row 4151 confirms `全局时停` through 300F.
- Heavy Inversion uses rows 4135 and 4136. It remains `action_time = 1.3` and `combat_time_cost = 1.3` because row 4135 has `时停`, not `全局时停`.
- Mornye Intro Convergence uses rows 4148, 4149, and passive row 4164. It remains a non-policy transition event with `action_time = 1.7`, `combat_time_cost = 1.7`, base Concerto +10, passive Concerto +20, and final Concerto +30. The workbook text currently says previous-character Outro at 36F; the source guard records this instead of silently changing it to 35F.
- Distributed Array uses rows 4143-4147. It gains base Concerto +10 and Relative Momentum +60 from four +15 rows.
- Observation A3 keeps its existing Relative Momentum behavior and receives the passive +20 Concerto from row 4164.

The optional simplified Interfered Marker mode remains `simplified_on_inversion`; direct Interfered Marker conversion from Inversion is not source-confirmed. The full Tune/Tune Rupture/Tune Strain system and 谐度破坏 behavior remain unimplemented beyond source-audit metadata.

This correction changes combat time, damage timing, and reward-producing damage totals for some Mornye routes. Existing PPO models trained before this patch are stale for valid comparison and should be retrained when using these corrected mechanics. No PPO training was performed for this patch.

## Mornye Intro Enabled Transition v1

Mornye Intro Convergence is implemented as a non-policy incoming transition event. It is never directly selectable by PPO and is not included in the policy action space; the selected action remains `swap_to_mornye`, while the resolved enabled transition action is `transition:mornye_intro_convergence`.

Mornye Intro only triggers when the outgoing character has full Concerto and Mornye's Intro/QTE mode is explicitly set to `enabled`. The default mode remains `disabled`. In `disabled` mode, the candidate may be logged but no Intro damage, time, resource gain, or Mornye state effects apply. In `dry_run` mode, the candidate is logged for review only and the generic fallback swap timing is still used. In `enabled` mode, the generic transition-action pipeline applies Convergence damage/time and v1 mechanics.

Implemented Mornye Intro values:

- `action_time = 1.7`
- `combat_time_cost = 1.7`
- hit multiplier `[2.0279]`
- base `concerto_energy_gain = 10` plus passive +20 from source row `角色-女!4164`, for final `concerto_energy_gain = 30`
- clears Rest Mass Energy
- enters Wide Field Observation for 30 seconds
- creates Syntony Field for 25 seconds

Outgoing Outro hooks still run before incoming Intro hooks. When an enabled incoming transition event applies and `consume_concerto_on_enabled_transition` is true, the outgoing character's Concerto is consumed. No-concerto swaps and disabled/dry-run modes continue to use fallback swap behavior.

Tune Break, Tune Rupture, Tune Strain, full Observation/Interfered Marker conversion, Proof of Boundedness, healing, DEF defensive calculations, and automatic Syntony Field periodic damage remain unimplemented. The optional simplified Interfered Marker amp mode is separate from full Tune conversion. No PPO retraining was performed.

## Party Training Transition Modes

Party simulations can now choose transition modes through party preset overrides, CLI flags, and the Streamlit UI. Defaults remain disabled unless a party preset or explicit override enables them. QTE/Intro actions are never policy actions: PPO still selects swap actions such as `swap_to_aemeath` or `swap_to_mornye`, and transition events are automatic consequences when Concerto and mode conditions allow them.

Mode behavior:

- `disabled`: logs candidates where available but ignores QTE/Intro damage, timing, and state effects.
- `dry_run`: logs reviewed transition candidates without affecting DPS.
- `enabled`: applies reviewed QTE/Intro transition events through the generic transition pipeline.

The `aemeath_mornye_enabled_test_party` preset enables Aemeath QTE, Mornye Intro, and Mornye Outro for deterministic transition-route testing. Generic swap timing in party presets remains placeholder metadata, not real gameplay timing.

CLI examples:

```bash
python rl/train_maskable_ppo.py --party aemeath_mornye_enabled_test_party --transition-mode enabled --timesteps 50000 --model-path models/maskable_ppo_aemeath_mornye_enabled_v1.zip
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_aemeath_mornye_enabled_v1.zip --party aemeath_mornye_enabled_test_party --transition-mode enabled
```

Specific flags override the broad transition mode:

```bash
python rl/train_maskable_ppo.py --party aemeath_mornye_enabled_test_party --transition-mode enabled --aemeath-qte-mode disabled
```

Models trained with different party rosters, action spaces, or transition-mode settings are not interchangeable. No PPO retraining is performed by the transition-mode support patch itself.

## Aemeath-lite Character Mechanic

Aemeath-lite is a first-pass architecture validation character, not a final real-game implementation. Common combat systems remain in simulator/. Aemeath-specific form state, combo state, action replacement, Synchronization Rate, Resonance Rate, Seraphic Duet, Overdrive, and Finale behavior live in characters/aemeath.py.

PPO and Demo Sequence select high-level actions such as aemeath_basic_attack, aemeath_resonance_skill, and aemeath_resonance_liberation. AemeathMechanic resolves those inputs into concrete internal actions such as Aemeath Form Basic Stage 1, Mech Basic Stage 2, Seraphic Duet, Overdrive, or Finale based on current Aemeath state. Concrete internal actions are hidden from PPO with policy_selectable = false.

Implemented Aemeath-lite scope:

- Aemeath Form and Mech Form
- Aemeath Form basic attack stages 1-4
- Mech Form basic attack stages 1-4
- Basic Attack resolution by current form and combo stage
- Resonance Skill replacement for normal Form Switch, Sync Strike, Seraphic Duet, and Finale
- Heavy Attack Charged I/II routing for Aemeath and Mech forms
- Synchronization Rate and Resonance Rate
- Seraphic Duet duration state
- Overdrive with Heavenfall Unbound and Stardust Resonance timers
- Starlume Acceleration and Instant Response state placeholders
- Heavenfall Edict: Finale replacement while Heavenfall Unbound is active and both resource limits are met
- Aemeath-specific PPO observation and Streamlit debug state

Not implemented yet:

- Starflux utility behavior and natural recovery
- Tune Break
- Tune Rupture damage and follow-up mechanics
- Fusion Burst damage and follow-up mechanics
- Fusion Trail / Rupturous Trail damage
- Trailblazing Star follow-up damage or mechanics beyond the implemented Aemeath 5-set runtime stat buff
- Rupturous Trail
- Stardust Resonance's full effects
- Heavy attacks
- Intro and Outro skills
- team-wide buffs
- full passive effects
- mid-air attacks and dodge counters
- exact real hit timings or final damage values

## Aemeath Resonance Mode Mechanic Events

Aemeath has a configurable `aemeath_resonance_mode` under `mechanics.aemeath` with supported values `unresolved`, `fusion_burst`, and `tune_rupture`. The default is `unresolved`, which emits no event and logs that the mode is unresolved. Streamlit exposes this selector for Demo Sequence and PPO Model evaluation; CLI training/evaluation can set `--aemeath-resonance-mode`.

In `fusion_burst` mode, source-backed trigger actions emit the `fusion_burst` event tag. In `tune_rupture` mode, they emit `tune_rupture_shifting`. The same skill can trigger once every 3 seconds, keyed by character, action, and trigger id. Multi-hit actions emit at most one event per action execution.

These event tags do not add Fusion Burst damage, Tune Rupture damage, Fusion/Rupturous Trail damage, Seraphic Duet follow-up damage, coefficients, timings, resources, cooldowns, or reward shaping. PPO reward remains `damage_this_action / 10000.0`.

## Aemeath Trailblazing Star Echo Set

`profiles.aemeath.aemeath_user_real_01` includes user-supplied Trailblazing Star metadata. Its 2-set Fusion DMG bonus is already included statically in the profile's element damage bonuses and is not added again at runtime.

The implemented 5-set runtime buff is triggered by emitted `fusion_burst` or `tune_rupture_shifting` events. The triggering damage receives the buff: +20% Crit Rate and +20% Fusion DMG for 8 seconds, with one stack and same-name refresh behavior.

The current simulator uses action-level aggregate damage for these trigger actions, so the whole triggering action is treated as receiving the buff as `same_action_aggregate_approximation`. This corrects the obsolete earlier rule where only later damage received the first activation.

Full Fusion Burst explosion damage, Tune Rupture damage, Fusion Trail, Rupturous Trail, Seraphic Duet extra damage, and Stardust Resonance extra effects remain unsupported.

Source-confirmed trigger metadata is currently stored from the user-supplied skill screenshot, not embedded workbook evidence. The source audit lives at `reports/aemeath_resonance_mode_mechanic_source_audit.md` and `data/extracted/aemeath_resonance_mode_mechanic_source_audit.json`.

## Aemeath-lite Data Accuracy

Aemeath-lite now uses Level 10 coefficients visible in the provided skill screenshots for:

- Aemeath Form basic attacks
- Mech Form basic attacks
- normal Form Switch and Sync Strike variants
- Seraphic Duet Overture and Encore
- Heavenfall Edict: Overdrive
- Heavenfall Edict: Finale

These values are still placeholders or approximations:

- most action_time values outside the confirmed whitelist below
- hit timing offsets
- Synchronization Rate gain values
- some mechanic effects beyond the implemented Aemeath-lite subset

Full Aemeath is not implemented yet. Starflux is utility-related and intentionally omitted from the current DPS-lite implementation. Starflux natural recovery/spending, Tune Break, Tune Rupture, Fusion Burst, Fusion Trail, Rupturous Trail, Stardust Resonance's full Trail effects, Heavy Attacks, Intro/Outro, team buffs, full passives, mid-air attacks, dodge counters, and exact video-verified hit timings remain out of scope.

Character mechanics have an advance_time hook that runs whenever action/internal time advances, even if the character is off-field. Aemeath Seraphic Duet, Heavenfall Unbound, Stardust Resonance, and Starlume Acceleration timers use this hook, so their remaining time decreases during swaps and during other characters' actions. Heavenfall Finale is separated from Overdrive cooldown by using its own cooldown group. Aemeath-lite has selected Level 10 screenshot coefficients, while several mechanic values remain placeholder/sample values.

The source-aligned coefficient pass applies two manually reviewed Excel C0/base alignments only: Overdrive uses `[2.008, 2.6774, 2.6774, 2.6774]`, and Seraphic Duet Encore uses source row order `[0.179, 0.179, 0.3579, 0.3579, 0.179, 0.179, 1.7893, 0.3579]`. Encore's total coefficient is unchanged. This pass does not change resources, action timing, combat timing, Heavy Attack timing, Form Switch timing, Sync Strike timing, simulator mechanics, or PPO/rewards.

The internal state field is still named `seraphic_duo_remaining` for compatibility with existing tests and saved debug output, but user-facing documentation and UI text should refer to the mechanic as Seraphic Duet.

## Aemeath Confirmed Time-Stop Timing

Some Aemeath cinematic actions have long action lock but reduced or zero timed-combat cost. The simulator intentionally separates `action_time` from `combat_time_cost`: `action_time` drives action lock, hit progression, buffs, anomalies, and character mechanic timers; `combat_time_cost` drives the timed-combat clock and cooldown reduction, and defaults to `action_time` when omitted.

Confirmed whitelist values currently applied:

- Overdrive: 4.3667s action_time / 0.0s combat_time_cost.
- Finale: 5.6667s action_time / 0.0s combat_time_cost.
- Seraphic Duet Overture/Overturn: 3.0s action_time / 1.3167s combat_time_cost.
- Seraphic Duet Encore: 2.4167s action_time / 1.3333s combat_time_cost.

Heavy Attack, Form Switch, and Sync Strike reviewed timings are also applied as described below.

## Aemeath Heavy / Form Switch / Sync Strike Timing

Reviewed Heavy Attack and Sync Strike timing values are applied without PPO retraining changes:

- Aemeath Form Charged I: 110F / 1.8333s action_time and combat_time_cost.
- Aemeath Form Charged II: 220F / 3.6667s action_time and combat_time_cost.
- Aemeath Form Charged II during Instant Response: 110F / 1.8333s action_time and combat_time_cost.
- Mech Form Charged I: 62F / 1.0333s action_time and combat_time_cost.
- Mech Form Charged II: 124F / 2.0667s action_time and combat_time_cost.
- Mech Form Charged II during Instant Response: 62F / 1.0333s action_time and combat_time_cost.
- Sync Strike: Armament Merge: 1.1667s action_time and combat_time_cost.
- Sync Strike: Call of Dawn: 0.9667s action_time and combat_time_cost.

Normal Form Switch is modeled as the immediate opposite-form Basic Attack Stage 1 rather than a separate 1.0s E1 action. Switching from Aemeath to Mech uses Mech Basic Stage 1 timing and hit multipliers, then sets the next Mech Basic Attack to Stage 2. Switching from Mech to Aemeath uses Aemeath Basic Stage 1 timing and hit multipliers, then sets the next Aemeath Basic Attack to Stage 2.

Instant Response Heavy Attack timing follows the manually reviewed frame values and is resolved before the after-action mechanic clears Instant Response. This preserves the existing rule that `combat_time_cost` affects timed-combat clock and cooldown reduction while `action_time` drives action lock, buffs, anomalies, and Aemeath mechanic timers.

## Aemeath Notice-Based Mechanics

Excel notice text is applied within the current Aemeath-lite scope:

- Normal E1 Form Switch immediately casts the opposite-form Basic Attack Stage 1 and shares a 1s `aemeath_form_switch` cooldown.
- The special post-Overdrive E1 switch from Mech to Aemeath immediately casts Aemeath Basic Attack Stage 2, then sets the next Aemeath Basic Attack to Stage 3.
- The E1 shared cooldown applies only to E1 form-switch actions, not Seraphic Duet, Sync Strike, Finale, or Overdrive.
- Synchronization Rate gains from Basic Attack, normal Form Switch, special post-Overdrive Form Switch, and Sync Strike are aligned to Excel notice/frame values under the full-hit DPS-lite assumption.
- Heavy Attacks are not assigned `sync_delta` by this notice-alignment patch.
- No PPO retraining was performed for these notice mechanics.

Current Aemeath-lite mechanic notes:

- Basic Attack Stage 4 in Aemeath Form or Mech Form grants Seraphic Duet for 5 seconds.
- If Seraphic Duet is active but Synchronization Rate is below 100, Resonance Skill performs the normal form switch, Seraphic Duet remains active, and the next Basic Attack in the new form starts from Stage 2.
- If Seraphic Duet is active and Synchronization Rate is 100 or higher, Resonance Skill performs Seraphic Duet Overture or Encore, consumes 100 Synchronization Rate, ends Seraphic Duet, switches form, sets the next Basic Attack in the new form to Stage 2, and grants 1 Resonance Rate.
- Normal Form Switch is separate from Sync Strike. Grounded Aemeath-lite normal Form Switch uses the resulting form's Basic Attack Stage 1 coefficients and sets the next Basic Attack to Stage 2.
- Sync Strike occurs only after eligible previous actions in a one-action window. Aemeath Basic Attack Stages 2-4 and Aemeath Heavy Attacks open Armament Merge; Mech Basic Attack Stages 2-4 and Mech Heavy Attacks open Call of Dawn. Exact real-time trigger windows are not implemented.
- Heavy Attack Charged I and Charged II are implemented for Aemeath and Mech. Charged I connects to Basic Attack Stage 2, and Charged II connects to Basic Attack Stage 3.
- Outside Instant Response, aemeath_heavy_attack resolves to Charged I. During Instant Response, it resolves to Charged II.
- During Instant Response and Heavenfall Edict: Unbound, Charged II restores 200 Synchronization Rate, ends Instant Response, and can enable Finale if Resonance Rate is also 4.
- Instant Response Heavy Attack damage amplification is approximated as x3.0 total direct hit damage in this simulator.
- Heavy Attack action_time values use the reviewed frame timings listed above, including Instant Response overrides.
- Heavenfall Edict: Overdrive deals Fusion DMG, recovers 30 Synchronization Rate and 1 Resonance Rate, switches to Mech Form, sets Mech Basic Attack to Stage 2, grants Stardust Resonance for 30 seconds, and grants Heavenfall Edict: Unbound for 60 seconds.
- Overdrive does not directly grant Seraphic Duet. The next Resonance Skill form switch after Overdrive connects to Aemeath Basic Attack Stage 2.
- If Starlume Acceleration is active, Overdrive recovers 1 additional Resonance Rate. The source and full behavior of Starlume Acceleration are not implemented yet.
- The next Seraphic Duet cast within 30 seconds after Overdrive does not consume Rupturous Trail / Fusion Trail. Full Trail systems are not implemented yet.
- Heavenfall Edict: Unbound replaces the Overdrive slot with Finale, but Finale is only available when Synchronization Rate is 200 and Resonance Rate is 4.
- When Finale is ready, Resonance Skill or Resonance Liberation casts Heavenfall Edict: Finale.
- When Heavenfall Unbound is active and Resonance Rate reaches 4, Aemeath enters Instant Response.
- Instant Response alone does not mean Finale is ready unless Synchronization Rate is also 200.
- After Overdrive from the initial state, Aemeath has only 30 Synchronization Rate and 1 Resonance Rate, so Finale is not immediately available.
  - Instant Response is removed when Heavenfall Unbound ends or after an Instant Response Charged II Heavy Attack.
- Finale depletes Synchronization Rate and Resonance Rate, ends Heavenfall Unbound, Stardust Resonance, and Seraphic Duet, and switches Aemeath back to Aemeath Form.
- Overdrive and Finale use separate cooldown groups and do not share cooldown.

## Aemeath Excel Data Extraction

The simulator can extract Aemeath action data from a source Excel workbook for verification. Put the workbook under:

```bash
data/source/
```

The extractor auto-discovers `.xlsx` files in `data/source`. The exact Chinese filename is not required; if only one workbook is present, it is used automatically. It also recognizes encoded zip-style filenames such as `#U9e23#U6f6e#U52a8#U4f5c#U6570#U636e#U6c47#U603b.xlsx` when choosing among multiple candidates. If discovery is ambiguous, pass `--workbook` with the intended path.

Run the extractor from the project root:

```bash
python scripts/extract_aemeath_excel_data.py
python scripts/extract_aemeath_excel_data_smoke_test.py
python scripts/aemeath_coeff_resource_extraction_smoke_test.py
python scripts/aemeath_qte_action_candidate_smoke_test.py
python scripts/aemeath_qte_intro_outro_extraction_smoke_test.py
```

The extraction script uses section tracking because the Aemeath character name may appear once as a section header while following action rows only contain labels like `A1`, `A2-1`, `E`, enhanced `E`, heavy attack labels, or liberation labels. Mapping uses the detected source action name first; full row text is not used for normal mapping, which avoids note/comment columns contaminating action IDs. QTE rows are explicitly excluded from normal form-switch/sync mapping and remain in the unmapped audit output. The QTE/Intro/Outro extractor writes `data/extracted/aemeath_qte_intro_outro_candidates.json` and `reports/aemeath_qte_intro_outro_review.md` for manual review only. It also writes `data/extracted/aemeath_qte_action_candidates.json` and `reports/aemeath_qte_action_candidate_review.md`, which split QTE-1/QTE-2/QTE-3 rows by Human Aemeath and Mech Aemeath sections into the proposed `aemeath_qte_intro_human` and `aemeath_qte_intro_mech` action candidates. This avoids mixing human/mech timing metadata. QTE candidates preserve raw Excel category fields and use a three-part classification: `trigger_classification` describes how the action enters rotation, such as `qte_intro`; `source_damage_label` preserves the Excel damage label, such as `intro_skill_damage` from `变奏伤害`; and `damage_bonus_category` is the future DPS calculation tag, such as `resonance_skill` or `none_or_unmodeled_intro`. Human QTE is QTE/Intro-triggered but has no confirmed modeled damage bonus category yet. Mech QTE is QTE/Intro-triggered and currently maps to `resonance_skill` for future bonus application because its raw skill category is `共鸣技能`. QTE-1/QTE-2/QTE-3 provide action candidate hit/timing rows; previous-character Outro trigger, cannot-switch text, and Flow Light 15-second state grants are recorded as metadata only. E1-QTE switch rows are metadata only and do not contribute QTE damage or timing. Aemeath QTE is not part of DPS simulation yet; a future patch must explicitly wire reviewed candidates into the transition pipeline.

Coefficient extraction reads explicit workbook multiplier columns when available. Numeric Excel cells are treated as already-normalized decimal multipliers; only strings that contain `%` are divided by 100. Explicit multihit notation such as `23.20%*3`, `23.20% x3`, or `0.232*3` is expanded into repeated coefficient segments, while unclear multihit rows remain conservative audit candidates. Repeat-hit information may live in the frame sheet while coefficients live in the skill/type sheet, so the extractor builds a repeat metadata index from frame rows and joins it to coefficient rows by character scope, normalized action label, and group action context. Joined repeat metadata is still review-only and does not modify `data/actions.json`. C0/C1/C2/C3 and other sequence or resonance-chain variants are preserved separately from base coefficients; C0 can be accepted as base for workbook rows whose labels are otherwise direct base damage rows. Dodge/counter, QTE, timing-only, bonus-effect, sequence, form-switch, and sync-strike rows are excluded from base coefficient candidates and kept in the unresolved audit output. Grouped frame rows are validated so action time is never earlier than the latest hit frame, and combat time subtracts only global time stop, not hitstop.

Resource extraction is conservative. The extractor records raw resource cells, parsed resource candidates, per-field confidence, and resource warnings. Low- or medium-confidence resource candidates are not patch recommendations unless manually confirmed. Coefficient candidates are also compared against current `data/actions.json` hit shapes as a safety guardrail: candidates shorter than current actions are never considered safe, and `safe_to_patch` means review-ready only, not automatically applied. Coefficient/resource review files are audit-only and do not modify `data/actions.json`; time-stop timing has already been handled separately. This pass generates:

- `data/extracted/aemeath_excel_actions.json`
- `data/extracted/aemeath_excel_unmapped_rows.json`
- `data/extracted/aemeath_coeff_resource_candidates.json`
- `data/extracted/aemeath_coeff_resource_unresolved.json`
- `data/extracted/aemeath_timing_candidates.json`
- `data/extracted/aemeath_timing_unresolved.json`
- `reports/aemeath_excel_diff.md`
- `reports/aemeath_coeff_resource_review.md`
- `reports/aemeath_timing_review.md`

Heavy/Form Switch/Sync Strike timing extraction is review-only and does not modify `data/actions.json`. Heavy Attack `action_time` candidates must include charge/preparation rows instead of only direct hit rows. Normal Form Switch timing uses normal E1 rows, while Sync Strike timing uses E2/合击 rows and keeps human and mech sections separate. QTE, Intro, Outro, Seraphic Duet, dodge/counter, and already-handled liberation rows are excluded from timing candidates and preserved in unresolved review output.

Later patches may apply confirmed coefficients, resource values, or timing values after the review files are manually reviewed.

Field meanings:

- `action_time`: time until the next action decision / cancel point.
- `combat_time_cost`: time deducted from timed combat mode.
- hit timing: damage occurrence times within the action.
- time stop segments: global time stop / cinematic time stop data.
- hitstop: impact pause data, recorded but not used in DPS calculation yet.

## Character Selection

The simulator supports selecting which characters are active for training, evaluation, deterministic simulation, and Streamlit. PPO action space is built only from the selected characters' policy-selectable actions. Concrete internal actions remain hidden from PPO and are used only after character mechanic resolution.

By default, the roster prefers Aemeath when available. Main DPS, Sub DPS, Support, Dummy Support, and Dummy Sub DPS are retained as dummy sample characters with intentionally low coefficients for system testing. They are not intended for real DPS analysis. Aemeath is the first partial real character implementation. Party presets can be selected with `--party aemeath` or `--party aemeath_test_party`.

Models are roster-specific because both action space and observation shape can change when selected characters change.

Train Aemeath only:

```bash
python rl/train_maskable_ppo.py --timesteps 50000 --character-ids aemeath
```

Evaluate Aemeath only:

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip --character-ids aemeath
```

Train dummy sample trio:

```bash
python rl/train_maskable_ppo.py --timesteps 50000 --character-ids main,sub,support
```

Evaluate dummy sample trio:

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip --character-ids main,sub,support
```

## Damage Formulas

The formula layer lives in simulator/damage_formula.py and currently supports normal damage, Tune Break damage, and simplified attribute anomaly tick damage.

Normal Damage =
Skill Multiplier x Scaling Value x DMG Bonus Multiplier x Expected Crit Multiplier x Boost Multiplier x RES Multiplier x DEF Multiplier x DMG Taken Multiplier x Final DMG Multiplier

`Scaling Value` is selected from the action's `scaling_stat`: `effective_atk`, `effective_def`, or `effective_hp`.

For each supported stat:

Base Total = Character Base + Weapon Base

Static Value = Base Total x (1 + Static %) + Static Flat

Effective Value = Static Value + Base Total x Runtime % + Runtime Flat

Expected Crit Multiplier = 1 + Crit Rate x (Crit DMG - 1)

Tune Break Damage =
Tune Break Base x Tune Break Multiplier x Tune Break Boost x RES Multiplier x DEF Multiplier x Tune DMG Bonus Multiplier

## Build Profiles

Build profiles are configurable stat overlays stored in `data/build_profiles.json`. `data/characters.json` remains the base/default character stat source, while build profiles add editable assumptions for a simulation run without changing character mechanics, action routing, timings, resources, or PPO policy actions.

Profile precedence is:

- CLI override
- Streamlit UI override
- party preset `build_profiles`
- character `default` profile in `build_profiles.json`
- existing `characters.json` stats

CLI examples:

```bash
python rl/train_maskable_ppo.py --party aemeath_mornye_enabled_test_party --build-profile aemeath:liberation_focus_test --build-profile mornye:support_er_cap
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip --build-profile aemeath:liberation_focus_test
```

Training and evaluation metadata include `active_build_profiles` and `effective_build_stats_summary`. Build profile changes affect damage and therefore PPO reward; models trained under different build profiles should not be compared blindly and should normally be retrained.

## Scaling Stat Components

Build profile schema v3 stores ATK, DEF, and HP components separately under `stat_components.atk`, `stat_components.def`, and `stat_components.hp`. Older ATK-only fields such as `character_base_atk`, `weapon_base_atk`, `static_atk_percent`, `static_flat_atk`, and `final_attack_reference` still work as legacy aliases for `stat_components.atk`.

Each damage action declares `scaling_stat`:

- `atk` uses `effective_atk`
- `def` uses `effective_def`
- `hp` uses `effective_hp`
- `none` is non-damaging or not coefficient-scaled
- `unresolved` blocks real/manual profile validation

`scaling_stat` and `damage_bonus_category` are different. `scaling_stat` chooses the ATK/DEF/HP base value multiplied by the coefficient. `damage_bonus_category` chooses the additive damage bonus bucket, such as Resonance Liberation DMG Bonus.

`final_reference` values are validation-only for all stats. They are compared against calculated static values, but are never multiplied, buffed, or used as the primary damage source. Runtime stat bonuses apply to that stat's `base_total`, not to final references.

Mornye is modeled as DEF-scaling based on user-provided skill description screenshots. The screenshot source is not embedded in this project yet, so affected actions are marked with `scaling_stat_source_status = user_supplied_screenshot_not_embedded`; see `reports/mornye_scaling_stat_source_note.md`.

Current component profiles such as `aemeath:component_test`, `aemeath:liberation_focus_test`, `mornye:support_er_component_test`, and `mornye:support_er_cap` are `test_assumption` profiles. They are useful for simulator and RL plumbing, but they are not verified real-game stat builds. Models trained with test profiles should not be treated as final balance results.

Manual real-stat profiles exist as `aemeath:aemeath_real_manual` and `mornye:mornye_real_manual`. They are marked `user_supplied_required` and intentionally contain null required fields. Training and evaluation fail loudly if one of these incomplete profiles is selected. Mornye real profiles require DEF fields for DEF-scaling actions and cannot pass with only ATK fields filled.

Required manual stats for ATK-scaling characters:

- character ATK
- weapon ATK
- ATK%
- flat ATK
- final ATK reference

Required manual stats for DEF-scaling characters:

- character DEF
- DEF%
- flat DEF
- final DEF reference
- weapon DEF only if source/game data has it

Required manual stats for HP-scaling characters:

- character HP
- HP%
- flat HP
- final HP reference

All real/manual profiles also require crit rate, crit damage, Energy Regen, all damage bonus, elemental damage bonus if applicable, and basic/heavy/skill/liberation damage bonuses.

Do not let the assistant/Codex invent real stat values. Use in-game character screens or user-supplied build data to fill real profiles manually. Changing scaling stats or build profiles changes damage and PPO reward, so valid PPO comparisons require retraining under the selected profile set.

Quick stat testing can use repeated CLI overrides:

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip --build-profile aemeath:component_test --stat aemeath:static_atk_percent:0.72 --stat aemeath:static_flat_atk:430 --stat aemeath:final_attack_reference:2711
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip --build-profile mornye:support_er_component_test --stat mornye:def.percent:0.72 --stat mornye:def.flat:430
```

## Damage Type Bonuses

Normal damage now resolves additive DMG Bonus through three buckets:

```text
effective_damage_bonus =
  damage_bonuses.all
+ damage_bonuses.by_category[action.damage_bonus_category]
+ damage_bonuses.by_element[action.element or generic]
```

Supported damage bonus categories are `basic_attack`, `heavy_attack`, `resonance_skill`, `resonance_liberation`, `intro`, `outro`, `coordinated_attack`, and `other`. Missing keys default to `0.0`, so future characters can add only the buckets they need.

Mornye Outro remains an All DMG Amplification buff in the amplification bucket. Mornye Interfered Marker simplified mode remains an enemy DMG Taken amp. Neither is converted into additive `damage_bonus`.

## Action Type vs Damage Bonus Category

`action_type` and `damage_bonus_category` are intentionally separate. `action_type` controls action routing, cooldown grouping, policy identity, and character mechanics. `damage_bonus_category` controls which additive DMG Bonus bucket a build profile applies. If `damage_bonus_category` is missing, the simulator falls back to `action_type`; if the resulting value is unknown, it falls back to `other`.

This is separate from `damage_category`, which is used inside hit data for normal, Tune Break, and anomaly hit categories. Older timeline fields may still expose `damage_category` as a compatibility alias for the damage bonus bucket, but new diagnostics should prefer `damage_bonus_category`.

This is also separate from `scaling_stat`. For example, a DEF-scaling Mornye action can still have `action_type = resonance_liberation` and `damage_bonus_category = resonance_liberation`; the coefficient uses DEF, while the additive bonus bucket remains Resonance Liberation.

Examples:

- Aemeath Seraphic Duet remains mechanically `action_type = resonance_skill`, but its source `伤害类型 = 共鸣解放伤害`, so it uses `damage_bonus_category = resonance_liberation`.
- Aemeath Heavy Charged remains mechanically `action_type = heavy_attack`, but its source `伤害类型 = 共鸣解放伤害`, so it uses `damage_bonus_category = resonance_liberation`.

Build profile bonuses use `damage_bonus_category`, not the mechanical `action_type`. The timeline and evaluation summaries expose selected policy action, resolved action, mechanical action type, and damage bonus category separately. Existing PPO models trained before this classification fix are stale because damage and reward values can change; retrain before making valid PPO comparisons. No PPO training was performed for this patch.

## Aemeath Liberation Focus Test Build

`aemeath:liberation_focus_test` is an editable test assumption that adds Resonance Liberation DMG Bonus. It exists to test whether Aemeath's Liberation-heavy damage distribution is represented better by category-specific bonuses. The current numeric value is configurable and is not verified final live-game build data.

`mornye:support_er_cap` is a support-test build assumption that sets Energy Regen to `2.60` / `260%` through generic build profile data. Mornye-specific Energy Regen scaling remains in Mornye mechanics.

## Hit Timing Model

The simulator does not model animation playback time and does not include a general cancel system. For DPS and reinforcement learning, each action has:

- action_time: internal action progression and time until the next action decision.
- combat_time_cost: timed-combat timer cost, defaulting to action_time when omitted.
- hits: damage events that occur at offsets inside action_time.

Buffs, Havoc Bane, and other time-sensitive effects are evaluated at each hit time. For example, if Havoc Bane has 0.30 seconds remaining at action start, a hit at 0.20 receives its DEF reduction and a hit at 0.45 does not. Current hit timing data is dummy/sample data; real character-specific hit timings are not implemented yet.

Source patches must distinguish global time stop from plain time stop. For Mornye, only workbook `AC = 全局时停` reduces combat timer loss; workbook `AC = 时停` alone is logged as non-global time stop and keeps its source frame duration as `combat_time_cost`.

## Cooldown Timing Model

Cooldown reduction follows `combat_time_cost`, not `action_time`. Normal actions without an explicit `combat_time_cost` still reduce cooldowns by their action time through the fallback behavior. Global time-stop actions such as Overdrive and Finale have long `action_time` but `0.0` `combat_time_cost`, so they do not advance the timed combat clock or reduce cooldowns during their cinematic time. This prevents time-stop cinematics from artificially shortening cooldown cycles.

## Timed Combat Cutoff

`combat_time` is hard-capped by the configured combat duration, which defaults to 120s. `action_time` may still describe animation lock, internal progression, hit timing, buffs, anomalies, and character mechanic timers, but the timed-combat clock never exceeds the cap. Final actions that cross the limit are clipped: cooldowns tick only by the effective `combat_time_cost` before the cap, damage after the cap is excluded, and the timeline records `effective_combat_time_cost`, `truncated_by_combat_limit`, `damage_before_cutoff`, and `damage_after_cutoff_excluded`. Actions with `combat_time_cost = 0` may still occur before the cap, but no action can be started after the episode is already finished.

## Attribute Anomaly System

- Actions apply anomaly stacks to enemy-wide CombatState.
- Active anomalies persist with simplified remaining_duration, tick_interval, and tick_timer values.
- Aero Erosion, Spectro Frazzle, and Electro Flare deal tick damage while active.
- Havoc Bane does not deal direct damage in this simplified implementation.
- Havoc Bane contributes defense reduction while active: def_reduction += stacks * 0.02.
- Anomalies applied by the current action start affecting and ticking on later actions, not the same action.
- Current durations, stack limits, tick intervals, and trigger behavior are simplified assumptions, not game-verified rules.

Supported anomaly types:

- aero_erosion
- spectro_frazzle
- electro_flare
- havoc_bane defense reduction

Monster-specific resistance data, character-specific special coefficients, hit timing, and full anomaly rules are not implemented yet. Current formulas are implemented as a reusable calculation layer with sample values.

## Simplified Rules

- Damage is split into normal_damage, tune_break_damage, anomaly_tick_damage, and total_action_damage in the timeline. Timeline rows also include action_time, combat_time_cost, effective_combat_time_cost, cutoff diagnostics, hit_count, and hit_details for debugging.
- damage/anomaly_damage remain compatibility fields and mirror total_action_damage/anomaly_tick_damage where appropriate.
- Damage uses expected crit value instead of random crit rolls.
- Damage is calculated using buffs and anomalies that are already active at the start of an action. Buffs and anomalies applied by the current action are added after the action resolves and affect later actions only.
- Existing buffs and active anomalies advance by action_time. Timed combat mode and cooldowns advance by effective_combat_time_cost when an action is clipped by the combat limit.
- Cooldowns are set after the action resolves, so cooldown timing currently starts from the end of the action.
- Actions may define cooldown_group. When present, cooldown checking and cooldown storage use that group key instead of action.id. Existing actions without cooldown_group keep their original behavior.
- Actions may define policy_selectable = false to hide concrete internal mechanic actions from PPO while keeping them available for mechanic resolution.
- Actions may define mechanic_effects. The common simulator stores this data but does not interpret character-specific effect keys.
- Resonance energy is capped by each character's resonance_energy_max, currently 125.0 in sample data.
- Concerto energy is capped at 100.0.
- Wasted resonance and concerto energy are tracked per character and per timeline action.
- Swapping to the currently active character is invalid and appears invalid in action masks.

## Reinforcement Learning

Maskable PPO is implemented with sb3-contrib. It is used because many actions are invalid depending on active character, cooldowns, resonance energy, and swap state. The environment exposes action_masks(), and training/evaluation use those masks.

The RL reward is intentionally simple and objective:

```text
reward = damage_this_action / 10000.0
```

damage_this_action is the simulator total_action_damage for the selected action, including normal, Tune Break, and active anomaly tick components that occur before or at the timed-combat cutoff. Resource waste, buff usage, cooldown usage, and action counts are analysis metrics only. They are not reward terms. Training is done by script, not inside Streamlit. Streamlit only evaluates a saved model in PPO Model mode. Demo Sequence mode is for deterministic simulator validation.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Train PPO

```bash
python rl/train_maskable_ppo.py --timesteps 50000
```

The default model output is models/maskable_ppo_wuwa.zip. Training metadata is written to results/training_metadata.json.

## Evaluate PPO

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip
```

Evaluation writes results/ppo_evaluation_summary.json and results/ppo_timeline.csv.

## Run Streamlit

```bash
streamlit run app.py
```

Streamlit supports Demo Sequence, PPO Model, and Character Mechanics modes. PPO Model mode loads and evaluates a saved model; it does not train.

## Character Mechanics Reference UI

The Streamlit app includes a Character Mechanics page. It currently supports Aemeath and documents the simulator's implemented interpretation rather than a complete game-client recreation. The page is data-driven from `data/mechanics/aemeath_mechanics.json` and covers modeled scope, omitted systems, resources, states, action resolution priority, timing, form switching, Heavy Attack, Sync Strike, Seraphic Duet, Overdrive / Finale, sync_delta values, and known limitations.

This reference page does not affect simulation results or PPO training. Update the mechanics JSON when character mechanics change.

## Checks

```bash
python -m compileall .
python scripts/generic_scaling_stat_component_smoke_test.py
python scripts/action_scaling_stat_damage_formula_smoke_test.py
python scripts/mornye_def_scaling_source_guard_smoke_test.py
python scripts/manual_real_profile_scaling_guard_smoke_test.py
python scripts/actual_stat_component_build_profile_smoke_test.py
python scripts/manual_real_profile_guard_smoke_test.py
python scripts/attack_runtime_buff_formula_smoke_test.py
python scripts/off_tune_buildup_rate_support_smoke_test.py
python scripts/mornye_halo_of_starry_radiance_5set_runtime_buff_smoke_test.py
python scripts/mornye_halo_of_starry_radiance_5set_metadata_smoke_test.py
python scripts/mornye_heal_event_trigger_smoke_test.py
python scripts/damage_formula_effective_attack_smoke_test.py
python scripts/aemeath_damage_bonus_category_source_smoke_test.py
python scripts/aemeath_resonance_mode_mechanic_event_smoke_test.py
python scripts/aemeath_resonance_mode_source_audit_smoke_test.py
python scripts/mornye_action_data_source_guard_smoke_test.py
python scripts/mornye_action_data_time_resource_smoke_test.py
python scripts/transition_actions_metadata_encoding_smoke_test.py
python scripts/mornye_character_smoke_test.py
python scripts/mornye_outro_buff_smoke_test.py
python scripts/mornye_party_integration_smoke_test.py
python scripts/mornye_mechanics_reference_smoke_test.py
python scripts/aemeath_qte_enabled_transition_smoke_test.py
python scripts/concerto_gated_transition_smoke_test.py
python scripts/party_state_foundation_smoke_test.py
python scripts/party_swap_smoke_test.py
python scripts/party_buff_smoke_test.py
python scripts/qte_intro_outro_foundation_smoke_test.py
python scripts/aemeath_party_integration_smoke_test.py
python scripts/rl_party_action_mask_smoke_test.py
python scripts/party_selection_smoke_test.py
python scripts/aemeath_mechanics_reference_smoke_test.py
python scripts/aemeath_source_aligned_coefficients_smoke_test.py
python scripts/aemeath_time_stop_timing_smoke_test.py
python scripts/aemeath_client_mechanics_smoke_test.py
python scripts/aemeath_coefficients_smoke_test.py
python scripts/aemeath_finale_condition_smoke_test.py
python scripts/aemeath_heavy_sync_strike_smoke_test.py
python scripts/aemeath_mechanics_correction_smoke_test.py
python scripts/aemeath_lite_smoke_test.py
python scripts/extract_aemeath_excel_data.py
python scripts/extract_aemeath_excel_data_smoke_test.py
python scripts/aemeath_qte_intro_outro_extraction_smoke_test.py
python scripts/aemeath_qte_action_candidate_smoke_test.py
python scripts/aemeath_action_timing_extraction_smoke_test.py
python scripts/aemeath_coeff_resource_extraction_smoke_test.py
python scripts/character_selection_smoke_test.py
python scripts/mechanics_smoke_test.py
python scripts/smoke_test.py
python scripts/hit_timing_smoke_test.py
python scripts/anomaly_smoke_test.py
python scripts/formula_smoke_test.py
python scripts/env_smoke_test.py
python scripts/rl_smoke_test.py
streamlit run app.py
```

## Project Layout

- app.py: Streamlit prototype UI with demo, anomaly notes, formula settings, PPO model evaluation, and character mechanics reference modes.
- characters/: Character mechanics plugin interface, default no-op mechanic, registry, and Aemeath-lite mechanic.
- data/: Dummy JSON data for characters, actions, enemy context, and buffs.
- simulator/: Core deterministic simulation logic, anomaly state system, and reusable damage formula layer.
- env/: Gymnasium environment, action masks, and objective damage reward.
- rl/: Maskable PPO training and evaluation scripts.
- scripts/: Smoke tests.
- results/: Training and evaluation artifacts.
- models/: Saved PPO models.

## Roadmap

1. Expand Aemeath-lite into fuller character-specific mechanics.
2. Add real character data.
3. Add monster-specific resistance and defense data.
4. Add proper intro, outro, concerto, and anomaly logic.
5. Tune Maskable PPO hyperparameters.
