# Mornye Off-Tune Buildup Rate Source Note

Default Off-Tune Buildup Rate is treated as 100% = 1.0 per user confirmation. This is stored as `support_stats.off_tune_buildup_rate` and is separate from Energy Regen.

Workbook row `角色-女!D4122` confirms Syntony Field grants all party members Off-Tune Buildup Rate +50%, with an additional +20% when C2 is unlocked. The C2 bonus is disabled by default and applies only when `mornye_constellation >= 2`.

Energy Regen is not Off-Tune Buildup Rate and is not used as a fallback for this stat.

The simplified Syntony Field healing proxy is based on workbook row `角色-女!D4120`, which records a healing check every 180F / 3 seconds during Syntony Field duration. The simulator uses field uptime at action boundaries as a DPS-evaluation proxy; exact healing amount and exact tick timing are not modeled.

High Syntony Field healing exists in the workbook, but High Syntony Field Off-Tune inheritance remains unresolved and is not applied unless a future source confirms inheritance.
