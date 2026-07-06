# Aemeath Mech Basic Stage 3 Repeat Resource Audit

- Action id: `aemeath_mech_basic_stage_3`.
- Repeat row: `角色-女!2890`.
- Repeat source: `角色-女!D2890`.
- Repeat count: 3.
- Off-Tune simple sum before patch: 58.06.
- Off-Tune repeat-aware value after patch: 62.54.
- Raw repeat-aware resonance energy: 1.96.
- Raw repeat-aware concerto energy: 3.91.
- Raw repeat-aware core resource: 18.54.
- Current simulator `resonance_energy_gain`: 7.
- Current simulator `concerto_energy_gain`: 6.
- Current simulator `sync_delta`: 18.54.
- Resource unit status: `simulator_resource_units_not_direct_excel_raw_values`.
- Resource numeric changes this patch: false.

## Interpretation

A3-2 checks once every 9F during active frames, up to three times, so Off-Tune is corrected from the simple row sum `6.7 + 2.24 + 2.24 + 46.88 = 58.06` to repeat-aware `6.7 + 2.24 * 3 + 2.24 + 46.88 = 62.54`.

The raw workbook repeat-aware resource values are recorded here for auditability, but simulator `resonance_energy_gain` and `concerto_energy_gain` are not changed because the project-wide conversion from raw workbook resource values to simulator resource units is not confirmed. Keep the simulator values at 7 and 6 until that conversion audit is proven.
