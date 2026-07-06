# Tune Break Excel Source Audit

Workbook inspected: `data/source/鸣潮动作数据汇总.xlsx`.

The current implementation uses a single-target boss-style Off-Tune cap of `3920`. That cap is recorded as a project default for the Endgame Matrix-style simulation, not as a fully audited enemy-table lookup.

Source-backed pieces:

- Off-Tune action values use `角色-女` column `S`.
- Aemeath Tune Break rows are `角色-女!C2802`, `C2804`, and `C2805`.
- Mornye Tune Break rows are `角色-女!C4155`, `C4157`, `C4158`, and `C4159`.
- Mornye Observation Marker / Interfered Marker text is `角色-女!D4164`.
- Mornye Syntony Field Off-Tune rate is `角色-女!D4122`.
- Aemeath and Mornye response mechanics are supported as trigger/cooldown logs; their damage remains unresolved.

Unresolved and deliberately not invented:

- Exact Tune Break cooldown and exact Off-Tune reset behavior.
- Full multi-target marker tracking.
- Exact non-boss enemy Off-Tune table selection.
- Exact Tune Strain stack behavior.
- Exact Aemeath Starburst and Mornye Particle Jet damage coefficients/timings.
