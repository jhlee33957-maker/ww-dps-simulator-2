# Aemeath Rupturous Trail Runtime Audit

Implemented C0 Rupturous Trail as a single-target enemy state for Tune Rupture. Successful actual party Tune Rupture response damage events grant 10 stacks, cap at 30, and refresh the aggregate combat-time duration to 30s.

Seraphic Duet snapshots target stacks and applies `1.0935 * (1 + 0.04 * stacks)` per hit. Normal follow-up repeats 5 hits; enhanced repeats 10 hits. Without preservation, Seraphic consumes all target stacks after snapshot. With preservation, it consumes the one-use preservation state and leaves target stacks intact.

Observation schema is now `slot_generic_mechanics_v5` with shape 314 and global target trail stack/remaining channels. v4/312 artifacts are intentionally incompatible.

Source audit: `data/source/aemeath_rupturous_trail_direct_audit_v98.json` (`078e9bc31ea540c2b4441d9e2e14681f1cdd74db834a8358ce25b8c7f38a4094`).
