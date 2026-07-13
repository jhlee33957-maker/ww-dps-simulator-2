# Beam Search v111 Infrastructure

Candidate 111 implements deterministic Beam Search infrastructure for the Wuthering Waves End Matrix DPS simulator. It remains pending external review and does not claim that a better route has been found.

## Why Beam Search Before MCTS

The simulator is deterministic, the legal policy actions are available at each state, and the objective is exact 120-second total damage. Beam Search is therefore easier to reproduce, audit, resume, and compare than stochastic MCTS. MCTS remains a later option if reviewed Beam Search proves too narrow or too myopic.

## Independence

The core search package expands only simulator-valid policy actions from the normal reset:

- party: `aemeath_mornye_lynae_enabled_test_party`
- initial active character: `aemeath`
- curriculum reset mode: `none`
- objective: `deterministic_120s_total_damage_only`

The core search does not read the manual route, BC demonstration NPZ, BC/PPO model files, policy probabilities, behavior-cloning loss, route similarity bonuses, action-agreement bonuses, or learned value functions. Manual/BC/PPO artifacts are comparison references only in reporting.

## State Handling

Search clones are produced by `clone_simulation_for_search`. The clone receives a compact future-state `CombatState` restore, fresh character mechanic objects, and an empty timeline. The runtime invariant `state.character_states is state.character_mechanics_state` is explicitly reconstructed after every clone and restore, using `character_mechanics_state` as the authoritative dictionary. Immutable action/config/build data is shared because future mutation is represented through `CombatState`. Historical timeline rows are omitted because future simulator behavior is driven by `CombatState`; final reporting can regenerate route timelines by replaying completed selected actions.

Search state is serialized as portable JSON-compatible data. Canonical node state contains future-affecting fields plus objective `total_damage`; diagnostic logs are restored to safe empty defaults. Frontier checkpoints are written atomically as JSON gzip files with SHA-256 validation. Pickle is not used as the canonical persisted format.

## Fingerprints And Diversity

Exact deduplication uses a deterministic future-state fingerprint over all `CombatState` fields classified as `future_affecting`. `total_damage` is classified as `objective_only`, so identical future states retain only the higher-damage path. Diagnostic logs are excluded. Floats are encoded with `float.hex()` before hashing. The 314-dimensional observation is not used as the exact fingerprint.

Coarse diversity grouping is separate from exact fingerprinting. Diversity keys include active character, combat-time band, resonance/concerto bands, enemy Off-Tune and Tune Break phase, key cooldown readiness, active buff signatures, scheduled-effect identity/remaining-duration/phase signatures, Aemeath setup state, Mornye setup state, Lynae setup state, shared Interfered/Strain state, and Rupturous Trail stack band. Scheduled-effect phase uses 0.5-second bands; scheduled-effect and active-buff remaining durations use 1.0-second bands. Short mechanic windows such as Aemeath Sync Strike and Overdrive switch windows encode active/inactive state plus 0.5-second bands. Standard short windows use 1.0-second bands, while long field states such as Syntony Field use active/inactive state plus a 5.0-second band. Quantization boundaries and per-field encoders are declared in `data/beam_search_plan_v111.json`.

## Corrected Time Buckets

The corrected runner maintains pending nodes by deterministic combat-time bucket and always processes the earliest nonempty bucket. Children are assigned to `floor(child.combat_time / time_bucket_width)`. Zero-combat-time children remain in the current bucket and are closed safely through exact fingerprint/no-state-change pruning and the expansion budget. Beam retention is applied within a bucket only; later-bucket nodes are not pruned against earlier-bucket nodes.

Resume manifests persist the plan SHA, stage configuration, actual immutable data hashes, all pending bucket checkpoint paths/hashes, completed buckets, completed routes, retained bucket resume queues, route lineage, counters, metrics, and log paths. Completed buckets are not recomputed on resume, and completed-route `completion_order` is monotonic across leaderboard truncation.

## Delayed Payoff

Pure current-damage pruning can discard setup states before buffs, resources, scheduled effects, or mechanics pay off. Candidate 111 keeps a route-blind diversity quota so low-current-damage setup states can survive long enough to prove useful. Diversity retention affects beam membership only; it does not add reward and cannot decide the final winner.

## Winner Rule

Completed routes are ranked only by final 120-second total damage. Within `1e-6`, the already externally verified immutable BC result wins. Otherwise the earlier completed search route wins. Route similarity is diagnostic only and is never a tiebreaker.

The full 120-second stage initializes final comparison with the verified BC incumbent. Partial frontier nodes are diagnostics and never become the project winner. Calibration stages report calibration metrics only and do not compare partial 30-second totals against the 120-second BC result.

Failure to exceed the verified BC/manual damage does not prove global optimality unless the entire reachable state space is exhausted without heuristic beam pruning. The default Beam Search plan cannot make that claim.

## Output Layout

Future execution writes to:

```text
results/beam_search_v111/
  search_state.json
  leaderboard.json
  best_route.json
  final_summary.json
  frontier/
  routes/
  logs/
```

Candidate 111 does not populate canonical Beam Search results.

## Horizon-Safe Reporting

Route replay summaries always record route hashes, action counts, event-aware attribution, and route-prefix diagnostics. Numeric total-damage comparisons against manual/BC/PPO references are emitted only when `combat_duration` is exactly 120.0 seconds. Three-second smoke routes and 30-second calibration routes set `reference_damage_comparison_status` to `horizon_mismatch_not_comparable` and do not emit 120-second damage ratios, deltas, or project-winner rankings.

## Memory Bound

The dry-run memory estimate derives concurrent bucket count from the maximum resolved combat-time cost in immutable action data:

```text
ceil(max_resolved_combat_time_cost / time_bucket_width)
  + current_bucket_allowance
  + bucket_safety_margin
```

For the 0.5-second bucket width, the max resolved combat-time cost is `2.6666666666666665` from `lynae_kaleidoscopic_mid_air_heavy`, so the required concurrent bucket count is 9.

Destination-bucket staging now uses a chunked exact accumulator keyed by future fingerprint before applying the same global-damage and diversity retention rule used by one-shot batch retention. Per-child arrival does only exact upsert into the current chunk; it does not materialize, sort, or scan the full retained set. The authoritative retained set is finalized only when processing the earliest bucket, writing a forced checkpoint, or writing final reporting.

When the in-memory unique-fingerprint threshold is reached, the accumulator atomically writes a compressed JSON gzip chunk under `frontier/accumulators/` and stores only the path, SHA-256, counts, node IDs, and byte metrics in `search_state.json`. Resume hash-validates those chunks and reconstructs the exact candidate set before finalization. This makes destination-bucket retention independent of child insertion order, batch partitioning, partition merge order, and resume serialization while keeping the main manifest and CLI output compact.

Accumulator metrics are conserved: `candidates_seen = exact_duplicates + unique_fingerprints`, and `unique_fingerprints = final_retained + final_rejected`. Exact duplicate replacements are reported as a subcategory of duplicate processing. Duplicate future-state route-lineage ties use a canonical `lineage_tie_key` before internal `node_id`.

The conservative dry-run estimates are:

- calibration: retained node bound 1,024, live node budget 9,216, accumulator unique fingerprint bound 8,192 per destination bucket, accumulator node budget 73,728, conservative memory budget 10,905,714,688 bytes.
- full 120s: retained node bound 4,096, live node budget 36,864, accumulator unique fingerprint bound 32,768 per destination bucket, accumulator node budget 294,912, conservative memory budget 43,619,713,024 bytes.

## Correction Validation

The corrected plan SHA is `b504def4e0c1da82ef2a6024d19ccac76fe175df51899e50d12f3bff99a17998`.

Focused correction guards include:

- `beam_search_clone_behavioral_parity_smoke_test.py`: replayed the 148-action verified route with restore-before-every-action parity, including step 27 resolving to `transition:aemeath_qte_intro_mech`.
- `beam_search_true_time_bucket_smoke_test.py`: verified earliest-bucket processing, zero-time bucket closure, and deterministic repeated output.
- `beam_search_state_payload_size_smoke_test.py`: verified compact payload sizes below 65,536 bytes and independence from diagnostic log growth.
- `beam_search_resume_equivalence_smoke_test.py`: verified uninterrupted 2000-expansion smoke equivalence to 1000 + resume-to-2000, including pending bucket payloads, route store, completion order, retained bucket queues, partial cursors, and leaderboard data.
- `beam_search_realistic_2000_resume_equivalence_smoke_test.py`: external-review named alias for the same realistic resume determinism guard.
- `beam_search_real_diversity_key_contract_smoke_test.py`: verified declared real setup-state categories affect the diversity key while remaining route-blind.
- `beam_search_short_window_diversity_smoke_test.py`: verified every externally flagged short mechanic window changes diversity between inactive 0 and active positive values, and that within-band/boundary behavior follows the declared field-specific encoders.
- `beam_search_horizon_comparison_guard_smoke_test.py`: verified 3s and 30s route reports suppress numeric 120s reference comparisons while 120s routes keep damage-only comparisons.
- `beam_search_hot_path_scalability_smoke_test.py`: verified peak metrics use per-node cached payload sizes and do not serialize full frontiers in the metric hot path.
- `beam_search_checkpoint_interval_smoke_test.py`: verified the declared checkpoint interval is honored, with initial/final manifest generations and dirty bucket frontier writes rather than every-bucket checkpoints.
- `beam_search_route_store_compaction_smoke_test.py`: verified the lineage store compacts to live pending/partial/completed-leaderboard/best-route closure and completed records remain compact.
- `beam_search_diversity_phase_contract_smoke_test.py`: verified scheduled-effect phase/remaining bands, trigger/payload/resource-policy fields, and active-buff source/target/remaining/stack fields affect diversity keys.
- `beam_search_future_field_classification_smoke_test.py`: verified objective/reporting/diagnostic fields are classified and audited, omitted from future payloads except `total_damage`, and do not affect future fingerprints.
- `beam_search_partial_node_resume_smoke_test.py`: verified expansion-budget interruption preserves unexpanded legal actions through node action cursors and resumes equivalently.
- `beam_search_final_replay_reporting_smoke_test.py`: verified deterministic route replay uses the party preset/build profiles, writes `routes/<route-id>_summary.json`, writes `routes/<route-id>_timeline.csv`, validates terminal parity before writing, and emits a complete verified BC incumbent manifest.
- `beam_search_terminal_replay_parity_smoke_test.py`: external-review named alias for the terminal replay parity guard.
- `beam_search_completed_route_reporting_contract_smoke_test.py`: verified replay reporting includes route comparison, reference comparison, action counts, data hashes, scheduled damage, and event-aware attribution fields.
- `beam_search_completion_order_smoke_test.py`: verified completion ordering remains unique and monotonic even after the completed-route leaderboard is truncated to 128 entries.
- `beam_search_memory_bound_contract_smoke_test.py`: verified the concurrent bucket bound is derived from action data and rejects undersized plan memory contracts.
- `beam_search_pending_frontier_bound_smoke_test.py`: verified a temporary 2,000-expansion calibration-config probe keeps every pending bucket within `beam_width` and total live nodes within `beam_width * concurrent_bucket_count`.
- `beam_search_peak_live_metric_smoke_test.py`: verified `peak_live_nodes >= live_node_count` in bounded execution output.
- `beam_search_intra_bucket_budget_guard_smoke_test.py`: verified wall-clock and memory interruptions inside bucket expansion preserve resumable state and resume to the uninterrupted result.
- `beam_search_destination_bucket_order_independence_smoke_test.py`: verified destination-bucket accumulator retention matches one-shot batch retention across adversarial insertion orders.
- `beam_search_destination_bucket_batch_equivalence_smoke_test.py`: verified accumulator output matches batch retention with duplicates, tie cases, and saturated global/diversity quotas.
- `beam_search_destination_bucket_partition_merge_smoke_test.py`: verified partitioned accumulator merges retain the same destination candidates regardless of merge order.
- `beam_search_destination_bucket_resume_equivalence_smoke_test.py`: verified serialized accumulator resume preserves retained candidates and route ancestry.
- `beam_search_diversity_quota_fill_smoke_test.py`: verified late-arriving high-damage duplicates cannot evict a rare setup state that should be retained by diversity quota fill.
- `beam_search_destination_accumulator_hot_path_smoke_test.py`: verified candidate insertion does not call full retained-set finalization and bounded execution keeps finalization count below expansion count.
- `beam_search_destination_accumulator_spill_smoke_test.py`: verified compressed chunk spill, SHA-backed restore, and exact one-shot retained equivalence.
- `beam_search_destination_accumulator_manifest_size_smoke_test.py`: verified accumulator nodes are absent from the main manifest, live in hashed compressed files, and bounded real output remains compact.
- `beam_search_compact_cli_output_smoke_test.py`: verified CLI stdout is a small summary with paths to canonical files and no frontier, route-store, accumulator, or timeline payloads.
- `beam_search_accumulator_metrics_contract_smoke_test.py`: verified exact duplicate, better replacement, diversity cap, diversity quota, and conservation metrics.
- `beam_search_duplicate_lineage_tie_smoke_test.py`: verified exact-duplicate lineage tie selection is stable across insertion permutations and uses the canonical lineage key before node ID.

## Commands

Dry-run, safe now:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v111.json `
  --dry-run-plan
```

Future calibration after candidate 111 external review:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v111.json `
  --execute `
  --only-stage calibration_30s
```

Resume calibration:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v111.json `
  --execute `
  --resume `
  --only-stage calibration_30s
```

Future full search only after calibration review:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v111.json `
  --execute `
  --only-stage full_120s
```

Do not run the full stage before calibration is externally reviewed.
