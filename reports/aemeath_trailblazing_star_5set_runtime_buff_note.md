# Aemeath Trailblazing Star 5-set Runtime Buff Note

Source status: user_supplied_set_tooltip

This patch implements only the conditional 5-set runtime buff for Aemeath's Trailblazing Star echo set.

The 2-set Fusion DMG bonus is already manually reflected in `profiles.aemeath.aemeath_user_real_01.damage_bonuses.by_element` and is not added again by runtime code.

Implemented behavior:

- If Aemeath has `echo_sets.trailblazing_star.pieces = 5` and `conditional_5set_enabled = true`, emitted `fusion_burst` or `tune_rupture_shifting` mechanic events apply `aemeath_trailblazing_star_5set`.
- The buff grants +20% Crit Rate and +20% Fusion DMG for 8 seconds.
- The buff has one stack and refreshes duration on repeated triggers.
- The buff is applied after the triggering action resolves, so the triggering hit does not receive the buff retroactively.

Unsupported or intentionally not implemented in this patch:

- Fusion Burst explosion damage.
- Tune Rupture damage.
- Fusion Trail or Rupturous Trail damage.
- Seraphic Duet trail removal or extra damage.
- Stardust extra mechanics.

The implementation consumes generic mechanic event tags and generic buff fields. It does not add Aemeath-specific branches to the damage formula.
