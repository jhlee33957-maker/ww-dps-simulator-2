# Aemeath Resonance Mode Mechanic Source Audit

Status: `user_supplied_skill_screenshot_not_embedded`

Implementation: `event_trigger_only`

This audit records the current source status for Aemeath Resonance Mode mechanic events. The simulator emits event tags only; it does not add Fusion Burst damage, Tune Rupture damage, Fusion/Rupturous Trail damage, Trailblazing Star set effects, Seraphic Duet follow-up damage, stat bonuses, coefficients, timings, resources, cooldowns, or PPO reward shaping.

## Source Review

- Checked workbook: `data/source/鸣潮动作数据汇总.xlsx`
- Checked fallback pattern: `data/source/#U9e23*.xlsx`
- Scanned sheets: `索引`, `角色-女`, `角色-男`, `角色技能类型`, `声骸`, `敌对属性列表`, `伤害配置`, `伤害计算`, `更新变动`, `附页1`, `附页2`, `base`, `prop`, `weapon`, `dmg`

The workbook and extracted Aemeath rows contain action, frame, coefficient, QTE, energy, and trail-related notes, but the current project source files do not clearly embed a cell that confirms the exact Fusion Burst / Tune Rupture - Shifting trigger mapping. Until that source is embedded, the trigger mapping remains marked as user-supplied screenshot evidence.

Reviewed rows include:

- `角色-女!2806`: Aemeath special energy and trail-related notes.
- `角色-女!2789-2792`: Human QTE frame rows.
- `角色技能类型!2726-2728`: Human QTE skill/type rows.
- `角色-女!2934-2936`: Mech QTE frame rows.
- `角色技能类型!2781-2782`: Mech QTE skill/type rows.

## Event Trigger Mapping

Damage actions with trigger metadata:

- `aemeath_basic_form_stage_3`
- `aemeath_basic_form_stage_4`
- `aemeath_mech_basic_stage_3`
- `aemeath_mech_basic_stage_4`
- `aemeath_sync_strike_armament_merge`
- `aemeath_sync_strike_call_of_dawn`

Transition-only QTE trigger metadata:

- `aemeath_qte_intro_human`
- `aemeath_qte_intro_mech`

Mode behavior:

- `fusion_burst`: emits `fusion_burst`
- `tune_rupture`: emits `tune_rupture_shifting`
- `unresolved`: emits no event and reports `aemeath_resonance_mode_unresolved_no_events_emit`

Cooldown behavior: the same skill can trigger once every 3 seconds. The cooldown key includes `character_id`, `action_id`, and `trigger_id`. Multi-hit actions emit at most one event per execution.

## Unsupported Follow-Up Mechanics

- `fusion_burst_explosion_damage`
- `fusion_trail`
- `rupturous_trail`
- `seraphic_duet_extra_tune_rupture_damage`
- `seraphic_duet_fusion_burst_multiplier`
- `stardust_resonance_extra_effects`
