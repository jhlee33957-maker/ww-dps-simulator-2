# Generic swap and Aemeath Outro v114

Candidate 114 is pending external review. This report documents only the user-approved transition-contract changes; it does not claim external verification or a global optimum.

## Generic swap contract

- A generic swap has exact `action_time = 0.0` and `combat_time_cost = 0.0`; it is not represented as 0.001 seconds.
- Source status is `user_approved_benchmark_assumption_after_workbook_and_web_review`.
- Generated policy actions retain the existing ordered 25-action policy and expose `cooldown = 1.0` with `cooldown_group = swap_reentry:<target>`.
- Availability checks the incoming target key. Execution starts only `swap_reentry:<outgoing> = 1.0` at swap input.
- Re-entry cooldowns live in `CombatState.cooldowns` and decrease only through effective combat time. Timed Intro/QTE time can consume the outgoing lock; a zero-time swap cannot.
- Exact zero-time swaps do not advance current/combat time, tick buffs or scheduled effects, reduce action/weapon/mechanic cooldowns, or generate damage/resources.
- The A→M→L zero-time test blocks both L→A and L→M until combat time advances. The 10k Beam probe independently confirmed loop safety and target-mask behavior.

## Aemeath Outro: Unseen Guard

- Transition event: `aemeath_outro_unseen_guard`; buff: `aemeath_outro_unseen_guard_all_damage_amp`.
- A full-Concerto outgoing Aemeath transition consumes Concerto once, removes every prior instance, snapshots Aemeath's resonance mode, and applies an independent 10% All DMG Amplification instance for 20 combat seconds to every non-Aemeath party member.
- Specific-character replacement identity is `(buff_id, target_character_id)`, so Mornye and Lynae instances coexist and same-target reapplication replaces only that target.
- In `tune_rupture`, recipient-emitted `tune_rupture_shifting` upgrades only that recipient to 20% total. In `fusion_burst`, recipient-emitted `fusion_burst` does the same.
- Upgrade is idempotent, does not refresh duration, and occurs after the triggering action. Action-start logs prove the triggering action used 10%, while subsequent actions see 20%.
- Aemeath receives no instance and cannot upgrade another recipient. `unresolved` mode still applies the shared 10% base but records that no mode-specific upgrade is allowed.
- Recast resets every recipient to 10%/20s before any later same-transition match; the timed Lynae Intro test then upgrades Lynae only after its damage.

## Deterministic v114 results

- Manual v114: 5,268,418.084869607 damage, 43,903.484040580064 DPS, +103,283.4025062481 damage versus v104.
- Manual route: 120.0 combat seconds, 164.53333333333336 current seconds, zero invalid actions, three base Outro casts, three disjoint recipient-upgrade annotations, and 95,899.63373681561 attributed direct-hit damage gain from Aemeath Outro.
- Recipient uptime: Mornye 55.75s at 10%; Lynae 26.60s at 10% and 29.15s at 20%.
- Existing-model winner: `models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip`, 5,276,844.358692044 damage / 43,973.70298910037 DPS.
- Full compact leaderboard: `results/transition_contract_v114_model_reevaluation/leaderboard.json`.

## Excluded-scope lock

- Mornye remains in `expectation_error_only`; no automatic counter success or Optimal Solution policy action was added.
- No dodge-counter or aerial policy action was added. Enemy death/waves remain out of scope.
- Reactor Husk remains hit 49F, uncancelled end 66F, and 1.1 seconds.
- Observation remains `slot_generic_mechanics_v5` shape 314; policy action count/order remains 25.
- No 3M/5M Beam Search, MCTS, BC training, or PPO training was run.

## Corrected low-memory spill selection

- The active v114 stage explicitly declares `accumulator_spill_format = streaming_jsonl_gzip_v113`; selection no longer depends on the old v113 stage ID.
- The real v114-stage contract test exceeds the 4,096-candidate in-memory threshold while making the legacy monolithic JSON-gzip writer fail if called. Streaming spill, restore, merge, resume, deterministic compressed hashes, and bounded serialization/restore buffers all pass.
- The corrected 10,000-expansion probe and its two-process repeatability test use the active v114 plan and report the resolved format and chunk schema. No v113 frontier is read or resumed.

## Future long-run commands (not executed)

First reviewed 3M run:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v114_32gb.json `
  --execute `
  --only-stage full_120s_lowmem_32gb_v114 `
  --max-expansions 3000000 `
  --output-root results\beam_search_v114_lowmem_32gb
```

Resume that same v114 root with the same 3M cap, or extend to 5M only after review by changing `--max-expansions` to `5000000`. The interrupted v113 root must never be resumed under v114.
