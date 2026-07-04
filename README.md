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

Generic swap actions are available for non-active party members. Party swaps are now treated as transition requests, not authoritative gameplay timing. `data/transition_config.json` and optional preset `generic_swap` metadata provide the current `0.50s` placeholder fallback; this intentionally overrides legacy `swap_to_*` action timings such as old `0.30s` dummy swaps. Timeline rows include transition metadata such as outgoing/incoming character IDs, transition events, placeholder timing source, fallback usage, and Intro/Outro event IDs.

The generic team buff foundation supports target scopes, optional tag filters, stat modifiers, and damage amp modifiers. `dummy_support` and `dummy_sub_dps` are test-only characters, not real Wuthering Waves data. `dummy_support_buff` applies a party damage amp buff for testing swap and buff persistence, while `dummy_support` also has a zero-time test-only outgoing Outro-like event that applies `dummy_support_outro_damage_amp` through the transition config. Mornye is the first real support character and applies `mornye_outro_recursion_all_dmg_amp` through her implemented Outro transition. Aemeath QTE/Intro/Outro rows are extracted section-locally for review only, ignoring QTE rows from other character sections, and remain disabled/non-executable. Raw Aemeath QTE rows are split into action-ready review candidates named `aemeath_qte_intro_human` and `aemeath_qte_intro_mech` when both workbook sections are present; they are proposed future transition actions, not executable simulator actions. Full real Intro/Outro/QTE timing, Starflux, Tune/Fusion/Trail systems, and real party rotations remain out of scope.

No PPO retraining was performed for this foundation patch. Saved PPO models are party/action-space specific and should be retrained before use with new party presets.

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
- simplified Resonance Skill behavior: baseline resolves to Optimal Solution; WFO resolves to Distributed Array
- Critical Protocol Resonance Liberation, including Syntony Field to High Syntony Field conversion
- Mornye Outro Recursion as a real transition buff: `mornye_outro_recursion_all_dmg_amp` gives the party 25% All DMG Amplification for 30s and consumes Mornye outgoing Concerto when applied

Not implemented in v1:

- full Tune Break / Tune Rupture / Tune Strain systems
- Interfered Marker damage amplification and Particle Jet response
- Proof of Boundedness defensive survival logic
- exact healing / DEF defensive value in DPS
- Energy Regen scaling for Mornye crit or team damage amp
- automatic Syntony Field damage scheduling
- full QTE/Intro state-machine details beyond reviewed transition data

Mornye Intro Convergence is present as reviewed transition data in `data/transition_actions.json` and remains disabled by default through `data/transition_config.json`. No PPO retraining was performed.

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
- Tune Rupture
- Fusion Burst
- Fusion Trail
- Rupturous Trail
- Stardust Resonance's full effects
- Heavy attacks
- Intro and Outro skills
- team-wide buffs
- full passive effects
- mid-air attacks and dodge counters
- exact real hit timings or final damage values

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

The source-aligned coefficient pass applies two manually reviewed Excel C0/base alignments only: Overdrive uses `[2.008, 2.6774, 2.6774, 2.6774]`, and Seraphic Duet Encore uses source row order `[0.179, 0.179, 0.3579, 0.3579, 0.179, 0.179, 1.7893, 0.3579]`. Encore's total coefficient is unchanged. This pass does not change resources, action timing, combat timing, Heavy Attack timing, Form Switch timing, Sync Strike timing, simulator mechanics, PPO/rewards, or Beam Search.

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
Skill Multiplier x Base ATK x ATK Multiplier x DMG Bonus Multiplier x Expected Crit Multiplier x Boost Multiplier x RES Multiplier x DEF Multiplier x DMG Taken Multiplier x Final DMG Multiplier

Base ATK = Character Base ATK + Weapon Base ATK

ATK Multiplier = 1 + ATK% + Flat ATK / Base ATK

Expected Crit Multiplier = 1 + Crit Rate x (Crit DMG - 1)

Tune Break Damage =
Tune Break Base x Tune Break Multiplier x Tune Break Boost x RES Multiplier x DEF Multiplier x Tune DMG Bonus Multiplier

## Hit Timing Model

The simulator does not model animation playback time and does not include a general cancel system. For DPS and reinforcement learning, each action has:

- action_time: internal action progression and time until the next action decision.
- combat_time_cost: timed-combat timer cost, defaulting to action_time when omitted.
- hits: damage events that occur at offsets inside action_time.

Buffs, Havoc Bane, and other time-sensitive effects are evaluated at each hit time. For example, if Havoc Bane has 0.30 seconds remaining at action start, a hit at 0.20 receives its DEF reduction and a hit at 0.45 does not. Current hit timing data is dummy/sample data; real character-specific hit timings are not implemented yet.

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
