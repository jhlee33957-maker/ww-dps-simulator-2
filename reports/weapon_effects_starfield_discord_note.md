# Weapon Effects: Starfield Calibrator and Discord

Starfield Calibrator and Discord weapon effects were added as runtime weapon effects. The system is data-driven and is intended to support future weapons by adding weapon definitions in `data/weapons.json`.

Runtime weapon effect logs use `weapon_effect_source_status = "user_supplied_weapon_tooltip"` for weapon source metadata so they do not collide with existing action or mechanic `source_status` fields.

User-entered static stats are treated as already reflected in build profiles. For `mornye_user_real_01`, Starfield Calibrator weapon base/static stats and its DEF% passive are metadata-only and are not applied again at runtime.

Starfield Calibrator R1:
- Resonance Skill restores 8 Concerto Energy to self.
- Concerto restore has a 20s per-character weapon-effect cooldown.
- Healing triggers party Crit DMG +20% for 4s.
- Same-name party Crit DMG effects do not stack; re-trigger refreshes duration.

Discord R1:
- Resonance Skill restores 8 Concerto Energy to self.
- Concerto restore has a 20s per-character weapon-effect cooldown.

Rank scaling is supported for R1-R5 for both weapons. Healing amount is not modeled; Starfield Calibrator uses existing `team_heal` events/proxies. Tune Break damage does not crit unless a future Tune formula source confirms otherwise.
