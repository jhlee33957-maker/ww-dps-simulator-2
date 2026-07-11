# Mornye Syntony Field Healing Scheduler Audit

## Scope

This audit covers the source-backed scheduled healing implementation for Mornye's normal Syntony Field and High Syntony Field. It replaces the canonical real-profile healing mode with `scheduled_180f_exact`; legacy proxy modes remain available only as deprecated diagnostics.

## Source References

- Normal Syntony Field source: `角色-女!4118`
- Normal Syntony Field healing source: `角色-女!4120 / 角色技能类型!533`
- High Syntony Field source: `角色-女!4119`
- High Syntony Field healing source: `角色-女!4121 / 角色技能类型!533`

## Timing

- Field duration: 1500 frames, or 25.0 combat seconds.
- First healing tick: 1 frame after field activation.
- Healing interval: 180 frames, or 3.0 combat seconds.
- Maximum heal count: 9.
- Relative healing frames: 1, 181, 361, 541, 721, 901, 1081, 1261, 1441.
- The theoretical next tick at frame 1621 is outside the 1500-frame field duration and is not emitted.

## Formulas

- Normal heal: `1805 + Mornye runtime DEF * 0.945`
- High Syntony Field C0 heal: `(1805 + Mornye runtime DEF * 0.945) * 1.40`
- Runtime DEF is evaluated from Mornye's effective buffed stats at the heal timestamp, not from the active target and not from a cached field-creation value.
- Target metadata: `host_action_actor_else_active_character`.
- Scheduled healing targets the resolved actor of the host action. Intro and generic swaps therefore target the incoming character. When no host actor is available, the currently active character is used. Mornye remains the source-stat owner.

Current reference values:

- Normal current-build runtime DEF: 2997.0536
- Normal current-build heal: 4637.215652
- High Field current-build runtime DEF with the existing +20% DEF effect: 3268.2536
- High Field C0 heal: 6850.8995128

## Healing Bonus and HP Model

- The current Mornye healing-bonus information is metadata-only.
- Numeric healing bonus applied by this task: 0.0.
- Diagnostic status: `healing_bonus_source_status = metadata_only_not_applied`.
- No HP-state model was introduced. The runtime logs `hp_application_mode = diagnostic_no_hp_state` and `effective_hp_restored = null`.
- C4's additional healing increase is excluded from this C0 task.

## Scheduler Integration

- Normal healing instance ID: `mornye_syntony_field_heal:mornye`.
- Normal payload action ID: `mornye_syntony_field_heal`.
- High healing instance ID: `mornye_high_syntony_field_heal:mornye`.
- High payload action ID: `mornye_high_syntony_field_heal`.
- Both payloads are non-policy scheduled healing payloads with zero damage, zero Off-Tune, zero Resonance Energy, zero Concerto Energy, and zero direct reward contribution.

Geopotential Shift creates the normal field at host frame 48. The first normal heal occurs at host frame 49, alongside the existing Damage 1 scheduled event in deterministic scheduler order.

Intro/QTE field creation uses transition combat end as the activation approximation. The first heal occurs at transition combat end +1 frame; there is no immediate heal at transition completion. The existing Damage 2 QTE restriction is preserved.

If an already scheduled heal becomes due during an Intro/transition host action, the heal targets the incoming transition actor rather than the outgoing active character. This preserves the transition lifecycle: `state.active_character_id` is still updated by the existing transition completion path.

Generic 0.5-second swaps use the incoming destination as the host actor. The generic swap itself is not a heal event, no proxy heal occurs at swap completion, and the actual active-character state update still occurs at its original point.

Critical Protocol replaces normal Syntony Field with High Syntony Field by canceling the normal heal schedule and scheduling the High heal schedule. Critical Protocol has zero combat-time cost, so no High heal occurs during the Liberation action; the first High heal occurs after the next positive combat-time progression reaches +1 frame.

Normal and High healing schedules are mutually exclusive and use `refresh_rule = replace`.

## Heal-Triggered Effects

Each scheduled heal tick emits exactly one existing team-heal mechanic event. That event drives the existing heal-trigger runtime paths:

- Halo of Starry Radiance 5-set activates on the first scheduled heal and refreshes on subsequent scheduled heals according to existing combat-time buff rules.
- No Halo activation occurs at field creation.
- No arbitrary action-boundary proxy refresh occurs in exact mode.
- Halo remains governed by its own duration and is not removed simply because the Syntony Field expires.

Weapon behavior:

- The real Discord R5 Mornye profile has no heal-triggered party weapon buff, so scheduled heals apply no heal-triggered weapon effect there.
- An explicit Starfield Calibrator test profile can trigger the existing `team_heal` party crit-damage buff on scheduled heal ticks.
- Starfield is not triggered by field creation or arbitrary action boundaries in exact mode.

## Legacy Modes

`field_creation_only` and `simplified_syntony_field_uptime` remain available as legacy diagnostic modes for focused compatibility tests. They are not source-exact and are not the default real-profile mode.

The canonical exact mode removes the `team_heal` mechanic tag from:

- `mornye_heavy_geopotential_shift`
- `mornye_liberation_critical_protocol`
- `mornye_intro_convergence`

Synthetic healing events for legacy modes are generated only by their explicit helper paths.
