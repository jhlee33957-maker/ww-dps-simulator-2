# Tune Break Runtime Note

- Enemy Off-Tune max: 3920 for the current single-target boss simulation default.
- Boss Tune Break cooldown: 3.0s, workbook-confirmed from `附页2!B227` for COST4/red-name targets.
- Cooldown behavior: Off-Tune accumulation is blocked entirely during Tune Break cooldown.
- Tune Break hit removes Mistune and the active shift state, resets the Off-Tune gauge to 0, and starts cooldown.
- Off-Tune value mappings are audited in `reports/off_tune_value_mapping_audit.md`.
