# Tune Break Excel Source Audit

Workbook inspected: user-provided Wuthering Waves-style source workbook.

The current implementation uses a single-target boss-style Off-Tune cap of `3920`. That cap is recorded as a project default for the Endgame Matrix-style simulation, not as a fully audited enemy-table lookup.

Source-backed pieces:

- Off-Tune action values use `角色-女` column `S`; see `reports/off_tune_value_mapping_audit.md`.
- Boss Tune Break cooldown is `3.0s` for COST4/red-name targets, sourced from `附页2!B227`.
- During Tune Break cooldown, Off-Tune accumulation is blocked entirely.
- Aemeath Tune Break rows are `角色-女!C2802`, `角色-女!C2804`, and `角色-女!C2805`.
- Mornye Tune Break rows are `角色-女!C4155`, `角色-女!C4157`, `角色-女!C4158`, and `角色-女!C4159`.
- Mornye Observation Marker / Interfered Marker text is `角色-女!D4164`.
- Mornye Syntony Field Off-Tune rate is `角色-女!D4122`.
- Aemeath and Mornye response mechanics are supported as trigger/cooldown logs; their damage remains unresolved.

Resolved runtime behavior:

- Tune Break hit removes Mistune and shift state.
- Tune Break hit resets the Off-Tune gauge to `0`.
- Tune Break hit starts the 3.0s boss cooldown.

Unresolved and deliberately not invented:

- Full multi-target marker tracking.
- Exact non-boss enemy Off-Tune table selection.
- Exact Tune Strain stack behavior.
- Exact Aemeath Starburst and Mornye Particle Jet damage coefficients/timings.
