# Mornye High Syntony Field Runtime Buff Note

Critical Protocol can create High Syntony Field when Syntony Field is present. Workbook `角色-女!D4150` says the Liberation destroys Syntony Field and generates High Syntony Field at frame 265, before the recorded Critical Protocol damage end frame, so the simulator uses action-level approximation for the whole Critical Protocol action.

High Syntony Field lasts 25 seconds. Workbook `角色-女!D4124` confirms the High Syntony Field DEF effect as party DEF +20%. The runtime implementation applies this as a team `def_percent` stat modifier, so DEF-scaling damage, including Mornye's own damage, uses increased `effective_def` while active. It is not a damage bonus and does not add ATK or HP.

High Syntony Field inherits Syntony Field's Off-Tune Buildup Rate boost. Syntony Field's source row is `角色-女!D4122` for party Off-Tune Buildup Rate +50%, with C2 +20% only when configured. The inherited High Syntony support keeps default current Off-Tune at 1.5 and therefore keeps Halo of Starry Radiance 5-set at the ATK +25% cap. Energy Regen remains separate from Off-Tune Buildup Rate.

High Syntony Field inherits Syntony Field healing behavior and has a +40% Healing Multiplier from user-supplied skill screenshot/source text. Exact healing amount and exact heal tick timing remain unmodeled. The current implementation uses the existing simplified field uptime `team_heal` proxy, so Halo 5-set can remain active through High Syntony Field uptime. Halo ATK% does not increase Mornye DEF-scaling damage.

Critical Protocol same-action behavior uses `same_action_high_syntony_field_creation_approximation`: if active Syntony Field exists when Critical Protocol is cast, High Syntony Field support buffs are applied before Critical Protocol damage calculation. Automatic Syntony/High Syntony field damage scheduling, exact healing amount/tick timing, defensive survival value, and full Tune Break / Interfered systems are not implemented in this patch.
