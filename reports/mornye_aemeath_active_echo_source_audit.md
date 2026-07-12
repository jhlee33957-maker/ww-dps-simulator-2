# Mornye/Aemeath Active Echo Source Audit v102

- Baseline archive: `ww-dps-simulator-2(102).zip` (`ca2c64e2a408737f0c407a10b9c44071fe5cc01d64f538af541bdebfd525a99c`)
- Workbook SHA-256: `81604978551989b5575e2d637ad4dfeb8c3b3b34d48e00a9ea79e9008c62f1f9`
- Implemented policy actions: `mornye_echo_reactor_husk`, `aemeath_echo_sigillum`
- Implemented non-policy scheduled payloads: `aemeath_echo_sigillum_hit_1`, `aemeath_echo_sigillum_hit_2`

## Mornye Reactor Husk

- Sources: `声骸!383`, `dmg!2534`
- Transformation Echo, one hit at frame 49, action/combat time 66 frames (1.1s).
- Fusion Echo Ability ATK-scaling hit, multiplier 3.51, base Resonance Energy 4.87.
- Real profile Energy Regen remains 2.5424; expected final gain is 12.381488.
- Off-Tune remains 0.0 with unresolved Echo Off-Tune source status.

## Aemeath Sigillum

- Sources: `声骸!410`, `声骸!411`, `dmg!2632`, `dmg!2633`
- Summon Echo activation is zero-time auxiliary policy action; source frame 80 is metadata/lifetime only.
- Activation schedules hit 1 at +25 frames and hit 2 at +55 frames using the combat-time scheduler.
- Hit 1: multiplier 0.684, base Resonance Energy 0.23, final 0.276 at Aemeath ER 1.2.
- Hit 2: multiplier 2.052, base Resonance Energy 2.13, final 2.556 at Aemeath ER 1.2.
- Off-Tune remains 0.0 with unresolved Echo Off-Tune source status.

## Guards

- Observation version remains `slot_generic_mechanics_v5`; shape remains 314; max policy action slots remains 32.
- Aemeath Resonance Liberation category bonus remains 0.688 and Mornye Energy Regen remains 2.5424; Echo passives are profile metadata only.
