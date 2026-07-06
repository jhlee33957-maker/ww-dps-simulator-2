# Everbright Polestar Weapon Effect Note

- Everbright Polestar is added as Aemeath's weapon runtime effect.
- Weapon base ATK and crit stat are assumed already reflected in `aemeath_user_real_01`.
- R1 All Attribute DMG Bonus is +12%.
- R1 conditional Resonance Liberation DEF Ignore is +32%.
- R1 conditional Resonance Liberation Fusion RES Ignore is +10%.
- Trigger events: `tune_rupture_shifting` or `fusion_burst`.
- Conditional duration: 8s.
- The conditional effect is not applied to Tune Break or Tune Response formula damage.
- DEF Ignore affects the DEF Multiplier denominator.
- RES Ignore affects the RES Multiplier through effective RES before the existing piecewise formula.
- Source status: `user_supplied_weapon_tooltip`.
