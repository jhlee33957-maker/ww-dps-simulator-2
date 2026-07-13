# Lynae Spray Paint Scheduler Audit

## Scope
- Host action: `lynae_visual_impact`.
- Payload action: `lynae_spray_paint_flux_application`.
- Scheduled event type: `status_application`.
- Target assumption: `single_target_remains_inside_paint_area`.
- C1 rows `角色-女!2685`, `角色-女!2686`, `角色-女!2687`, and `角色-女!2688` are out of scope and intentionally excluded from the S0 implementation.

## Timing
- Field creation occurs at the resolved Visual Impact combat end.
- Field duration is `300F` combat time.
- First check is `+1F`.
- Check interval is `120F`.
- Applications occur at relative frames `[1, 121, 241]`.
- No `+361F` check is scheduled.
- The scheduler keeps the field state visible until the `300F` combat-time duration expires even after the third and final application.

## Status Application
- Spray Paint is a periodic status application, not periodic damage.
- Each check reapplies `lynae_photocromic_flux` for `25s`.
- Each event has zero damage, Off-Tune, resource gain, cooldown, and reward contribution.
- Visual Impact's direct Photocromic Flux application remains unchanged.

## Mode Snapshot
- The field snapshots Lynae's resonance mode when Visual Impact creates the field.
- `tune_strain` maps to `tune_strain_shifting`, source row `角色-女!2683`.
- `tune_rupture` maps to `tune_rupture_shifting`, source row `角色-女!2684`.
- Later live mode changes do not affect existing scheduled field events.
- Recasting Visual Impact replaces the existing field and snapshots the new mode.

## Traceability
- Runtime event type: `scheduled_status_application`.
- Runtime events include scheduled effect id, instance id, payload id, host action context, combat-time offsets, trigger index, mode snapshot, applied target shift state, previous/new target shift duration, source status/ref, and target assumption.
- `spray_paint_window_remaining` is a scheduler-backed mirror of the active field remaining duration.
