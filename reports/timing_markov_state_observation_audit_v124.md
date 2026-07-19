# Candidate 124 timing Markov-state observation audit

Account observation remains `slot_account_constellation_single_boss_v6` with shape `330`. It was not modified in Stage 1.

The corrected runtime introduces hidden future-affecting state. Observation v7 is required before BC, PPO, Beam, or MCTS; training and search under v6 are blocked.

| Runtime item | In v6 | Derivable | Risk | Recommended compact v7 field |
|---|---:|---:|---|---|
| ongoing action owner | false | false | high | `ongoing_action_owner_slot` |
| ongoing action source ID or behavior class | false | false | high | `ongoing_action_behavior_class` |
| time until same-character input unlock | false | false | high | `same_input_lock_remaining` |
| time until swap unlock | false | false | high | `swap_lock_remaining` |
| time until action end | false | false | high | `action_end_remaining` |
| character persistence after swap | false | false | high | `persistent_off_field_owner_slot` |
| time until persistence cutoff | false | false | high | `persistence_cutoff_remaining` |
| pending packet count | false | false | high | `pending_packet_count` |
| time until next packet | false | false | high | `next_packet_time_remaining` |
| time until final packet | false | false | high | `last_packet_time_remaining` |
| pending packet behavior class | false | false | high | `pending_packet_behavior_class` |
| pending damage/resource/marker/buff flags | false | false | high | `pending_packet_effect_flags` |
| character re-entry cooldowns | true | true | low | `character_reentry_remaining_by_slot` |

Raw packet arrays must not be placed in the observation; use bounded counts, time summaries, behavior classes, and effect flags.

v6 labels SHA-256 before/after: `b32bfb6fc3287ccf10bef65b9ac146902c69cb0b1ce6808ef0acadf7bc50e374` / `b32bfb6fc3287ccf10bef65b9ac146902c69cb0b1ce6808ef0acadf7bc50e374`.
v6 deterministic initial-vector SHA-256 before/after: `6ccc4a5f228329c7b02ed72d4b1354cffc0c8a222d0ed1115be40316a18b3a4f` / `6ccc4a5f228329c7b02ed72d4b1354cffc0c8a222d0ed1115be40316a18b3a4f`.
