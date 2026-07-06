# Tune Break Runtime Note

- Enemy Off-Tune max: 3920 for the current single-target boss simulation default.
- Boss Tune Break cooldown: 3.0s, workbook-confirmed from `附页2!B227` for COST4/red-name targets.
- Cooldown behavior: Off-Tune accumulation is blocked entirely during Tune Break cooldown.
- Tune Break hit removes Mistune and the active shift state, resets the Off-Tune gauge to 0, and starts cooldown.
- Response event order: Tune Break damage first, final Tune Break hit applies `tune_rupture_interfered`, Observation Marker applies Interfered Marker if present, party responses scan, then response damage is applied immediately before the next policy action. Source status: `excel_event_order_derived`.
- Aemeath Starburst response: multiplier 5.9643, base 10000, Fusion Tune response damage, 8s cooldown.
- Mornye Particle Jet response: multiplier 2.9822 at C0, multiplier 7.7536 at C5+, base 10000, Fusion Tune response damage, 8s cooldown.
- Tune Break hits do not receive a newly applied Interfered Marker amp; response damage receives it when the marker was applied before the response scan. The response formula source remains `workbook_confirmed`.
- Off-Tune value mappings are audited in `reports/off_tune_value_mapping_audit.md`.
