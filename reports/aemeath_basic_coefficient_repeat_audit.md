# Aemeath Basic Coefficient Repeat Audit

## Summary

- Target action: `aemeath_mech_basic_stage_3`
- Old implemented hit multipliers: `[0.0389, 0.0389, 0.0389, 0.0389, 0.0389, 0.0389, 0.8154, 0.6165]`
- Old total: `1.6653`
- Corrected hit multipliers: `[0.1165, 0.0389, 0.0389, 0.0389, 0.0389, 0.8154]`
- Corrected total: `1.0875`
- Removed unsupported hit: `0.6165`

## Source Rows

| Segment | Skill source | Frame source | Multiplier | Repeat interpretation |
| --- | --- | --- | ---: | --- |
| A3-1 | `角色技能类型!I2746` | `角色-女!C2889:S2889` | `0.1165` | single hit |
| A3-2 | `角色技能类型!I2747` | `角色-女!C2890:S2890` | `0.0389` | `角色-女!D2890` says max 3 hits |
| A3-3 | `角色技能类型!I2748` | `角色-女!C2891:S2891` | `0.0389` | single hit |
| A3-4 | `角色技能类型!I2749` | `角色-女!C2892:S2892` | `0.8154` | single hit |

The extracted coefficient review also records the repeat join as `frame_sheet_join` from frame row `2890`, expanding A3-2 to three `0.0389` hits. No inspected workbook row supports the previous trailing `0.6165` hit for Mech Basic Stage 3.

## Off-Tune And Resource Repeat Interpretation

`aemeath_mech_basic_stage_3.off_tune_value` is corrected to repeat-aware `62.54` with source ref `角色-女!S2889:S2892` and repeat source `角色-女!D2890`. The old simple frame-row sum was:

`6.70 + 2.24 + 2.24 + 46.88 = 58.06`

With A3-2's Off-Tune contribution repeated three times, the corrected value is:

`6.70 + (2.24 * 3) + 2.24 + 46.88 = 62.54`

This patch does not change simulator resource gains. The repeat-aware raw workbook resource values are recorded in `data/extracted/aemeath_mech_basic_stage_3_repeat_resource_audit.json`, but the project-wide conversion from raw workbook resource columns to simulator `resonance_energy_gain` and `concerto_energy_gain` remains unresolved.

## Nearby Basic Action Audit

Nearby Aemeath basic action multipliers remain unchanged. The existing extracted coefficient review and coefficient smoke test agree on these expanded hit shapes:

| Action | Current multipliers | Total | Status |
| --- | --- | ---: | --- |
| `aemeath_basic_form_stage_1` | `[0.4635]` | `0.4635` | unchanged |
| `aemeath_basic_form_stage_2` | `[0.1389, 0.2084, 0.3473]` | `0.6946` | unchanged |
| `aemeath_basic_form_stage_3` | `[0.0932, 0.0932, 0.0932, 0.1863, 0.4656]` | `0.9315` | unchanged |
| `aemeath_basic_form_stage_4` | `[0.0673, 0.0673, 0.0673, 0.0673, 0.0673, 1.0094]` | `1.3459` | unchanged |
| `aemeath_mech_basic_stage_1` | `[0.232, 0.232, 0.232]` | `0.6960` | unchanged |
| `aemeath_mech_basic_stage_2` | `[0.1857, 0.7426]` | `0.9283` | unchanged |
| `aemeath_mech_basic_stage_4` | `[0.4038, 0.9421]` | `1.3459` | unchanged |
