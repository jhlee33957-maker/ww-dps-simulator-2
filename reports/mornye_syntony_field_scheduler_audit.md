# Mornye Syntony Field Scheduler Audit

## Scope

This report covers only source-confirmed normal Syntony Field deployment damage:

- Damage 1: `mornye_syntony_field_damage`
- Damage 2: `mornye_syntony_field_target_damage`

Exact 180-frame field healing remains out of scope and is still represented by the existing simplified action-boundary heal/Halo proxy.

## Source Traceability

Readable source references used by this implementation:

- `角色-女!4117`
- `角色-女!4118`
- `角色-女!4125`
- `角色-女!4126`
- `角色-女!4127`
- `dmg/角色技能类型!2655`
- `dmg/角色技能类型!2656`

## Field Creation Timing

Geopotential Shift (`mornye_heavy_geopotential_shift`) creates Wide Field Observation at source action frame 48. The normal Syntony Field deployment-damage scheduler therefore uses:

```text
activation_combat_time = host combat start + 48 / 60
```

Intro/QTE (`mornye_intro_convergence`) is source-confirmed to create Syntony Field, but the supplied frame rows do not isolate the creation frame. The implemented timing is the documented approximation:

```text
activation_combat_time = transition combat end
status = source_confirmed_creation; activation_timing_approximation_action_end
```

## Damage 1

Payload action: `mornye_syntony_field_damage`

- One scheduler payload hit
- Multiplier: `0.3977`
- Category: Resonance Liberation damage
- Element: Fusion
- Scaling: DEF
- Resonance Energy: `0`
- Concerto Energy: `0`
- Off-Tune: `0`

Schedule relative to field activation:

```text
first tick = 1 frame
interval = 27 frames
max trigger count = 5
source duration = 120 frames
relative frames = 1, 28, 55, 82, 109
```

## Damage 2

Payload action: `mornye_syntony_field_target_damage`

- One scheduler payload hit
- Multiplier: `0.9902`
- Category: Heavy Attack damage
- Element: Fusion
- Scaling: DEF
- Base Resonance Energy: `2.08`
- Concerto Energy: `6.65`
- Off-Tune: `66.4`

Schedule relative to field activation:

```text
one event at 23 frames
max trigger count = 1
remaining duration = 23 frames
```

The event is permitted to occur exactly at its expiration boundary and then the scheduled effect completes.

## QTE Restriction

Damage 2 is non-QTE only per source row `角色-女!4127`.

- Geopotential Shift schedules Damage 1 and Damage 2.
- Intro/QTE schedules Damage 1 only.
- Intro/QTE does not schedule the `0.9902` target event.
- Intro/QTE does not apply the `66.4` deployment Off-Tune or `2.08 / 6.65` resource event.

## Heavy Host Sequence

For Geopotential Shift, the field activates at host frame 48. Deployment events inside the Heavy Attack host are:

```text
frame 49: Damage 1
frame 71: Damage 2
frame 76: Damage 1
```

The source multiplier composition during the host is:

```text
0.3977 * 2 + 0.9902 = 1.7856
```

The full uncancelled deployment burst is:

```text
0.3977 * 5 + 0.9902 = 2.9787
```

## Resource And Off-Tune Attribution

Generic scheduled effects default to `scheduled_resource_policy = none`.

Only `mornye_syntony_field_target_damage` opts into:

```text
scheduled_resource_policy = source_confirmed_positive_gains
```

That policy applies only positive payload Resonance Energy and Concerto Energy gains to Mornye:

```text
final Resonance Energy = 2.08 * Mornye Energy Regen
Discord R5 Energy Regen = 2.5424
final Resonance Energy = 5.288192
Concerto Energy = 6.65
```

Concerto is not multiplied by Energy Regen. Normal caps and wasted-energy tracking still apply.

Damage 2 contributes raw Off-Tune `66.4`. With the C0 Syntony Field buildup-rate bonus active:

```text
66.4 * 1.5 = 99.6 applied Off-Tune
```

Damage 1 contributes no Off-Tune.

## High Syntony Field

When `mornye_liberation_critical_protocol` replaces an active normal Syntony Field with High Syntony Field:

- pending normal-field Damage 1 is removed;
- pending normal-field Damage 2 is removed if present;
- no High Syntony deployment-damage burst is scheduled.

Critical Protocol has zero combat-time cost, so pending normal-field ticks do not advance during the Liberation before replacement.

High Syntony retains its existing 25-second duration, DEF support, Off-Tune buildup-rate inheritance, and simplified healing metadata/proxy.

## Remaining Limitation

Exact 3-second Syntony/High Syntony healing is still not implemented. The current simplified heal/Halo proxy remains unchanged and should be replaced later by exact 180-frame scheduled heal events.
