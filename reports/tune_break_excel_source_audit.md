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
- Aemeath Starburst response damage is workbook-confirmed at multiplier `5.9643` from `角色-女!D2844`, `角色-女!C2880:D2880`, `角色技能类型!A2737:I2737`, and `dmg!A2590:C2590`.
- Mornye Particle Jet response damage is workbook-confirmed at C0 multiplier `2.9822` from `角色-女!D4181`, `角色-女!C4185:D4185`, `角色技能类型!A2676:I2676`, and `dmg!A2532:C2532`; C5 multiplier `7.7536` from `角色技能类型!A2677:I2677` is enabled only at `mornye_constellation >= 5`.
- Response damage uses base `10000`, response multiplier, Tune Response Boost, RES, DEF, Tune DMG Bonus, and target damage taken amp when present. Formula inputs and coefficients are `workbook_confirmed`; response amp timing is `excel_event_order_derived`, not a direct workbook statement. It does not use ATK/DEF/HP scaling, normal damage bonus categories, or ordinary Fusion DMG bonus.

Resolved runtime behavior:

- Tune Break hit removes Mistune and shift state.
- Tune Break hit resets the Off-Tune gauge to `0`.
- Tune Break hit starts the 3.0s boss cooldown.
- Final Tune Break hit applies `tune_rupture_interfered`, then Observation Marker applies Interfered Marker, then party responses scan and immediately add response damage before the next policy action.
- Tune Break hits that create Interfered Marker do not receive the newly applied amp. Response damage receives the new amp when Observation Marker was active before the response scan; this timing conclusion is derived from the Excel event order.

Unresolved and deliberately not invented:

- Full multi-target marker tracking.
- Exact non-boss enemy Off-Tune table selection.
- Exact Tune Strain stack behavior.
