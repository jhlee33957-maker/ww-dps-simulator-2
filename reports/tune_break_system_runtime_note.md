# Tune Break System Runtime Note

This patch implements a single-target Excel-based Off-Tune / Mistune / Tune Break flow.

- `enemy_off_tune_max = 3920` is the boss default for the current Endgame Matrix-style simulation.
- Off-Tune values come from Excel `角色-女` column `S`.
- Tune Break is a conditional character-specific policy action, not automatic damage.
- Aemeath uses Tune Break coefficients `1.0` and `12.0`.
- Mornye uses Tune Break coefficients `1.7334`, `2.2666`, and `12.0`.
- Tune Break damage uses the fixed base `10000` formula and does not use ATK/DEF/HP scaling.
- Interfered is applied after the final Excel-defined Tune Break hit.
- Mornye Interfered Marker is applied through Observation Marker + Tune Break and is modeled as target damage taken amplification.
- With Energy Regen `2.7944`, Mornye reaches the `40%` Interfered Marker cap.
- Party response scanning logs Aemeath Starburst and Mornye Particle Jet triggers/cooldowns. Their unresolved damage is not invented.
- `simplified_on_inversion` remains available as an explicit legacy approximation only.
