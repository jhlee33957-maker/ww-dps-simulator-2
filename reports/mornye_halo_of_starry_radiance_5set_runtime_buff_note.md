# Mornye Halo of Starry Radiance 5-set Runtime Buff Note

Halo of Starry Radiance 5-set is implemented as a party ATK% runtime buff triggered by `team_heal`.

Formula: `min(current_off_tune_buildup_rate * 0.20, 0.25)`.

Examples:

- Base Off-Tune 1.0 -> ATK +0.20.
- Syntony Field Off-Tune 1.5 -> ATK +0.25 cap.
- Syntony Field plus C2 Off-Tune 1.7 -> ATK +0.25 cap.

Duration is 4.0 seconds, max stacks is 1, and retriggers refresh duration/recalculate value instead of stacking.

Current team-heal support uses the simplified Syntony Field uptime heal proxy. Exact healing amount, exact 180F tick timing, defensive survival value, and full automatic Syntony Field damage scheduling are not implemented.
