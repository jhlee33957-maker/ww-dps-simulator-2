# Candidate 117: deterministic 32GB-safe MCTS design

Candidate 117 adds search infrastructure and a reviewed calibration plan. It does not contain a 20,000-simulation result, does not replace the completed Beam winner, and does not claim a global optimum.

## Why MCTS complements Beam

Beam Search retains a broad, explicitly bounded set of strong states at each search frontier. Pure UCT instead revisits a parent according to its mean completed-rollout reward plus uncertainty, so repeated evidence decides where later simulations are spent. This is an independent complementary validation method, not a continuation of the Beam route.

The MCTS core reads only simulator APIs, legal action masks, immutable action/config data, the shared compact state codec, and the fixed 25 policy actions. It does not read manual routes, demonstrations, models, RL results, Beam routes, Beam timelines, or Beam action ordering. The compact Beam manifest is read only by post-search comparison reporting. If it is absent, search still succeeds and comparison is marked unavailable.

## Search contract

Each simulation performs selection, at most one expansion, rollout, and backpropagation. A route is eligible only if the simulator reaches exactly 120.0 combat seconds. Its un-clipped terminal reward is `total_damage / 6000000.0`; UCT backs up the mean terminal reward, while maximum damage is tracked only for reporting.

For a visited child the score is `mean_reward + sqrt(2) * sqrt(log(max(parent_visits, 1)) / child_visits)`. Unvisited expanded children have priority. Progressive widening allows `min(legal_count, max(1, ceil(2 * sqrt(N))))` children at `N` parent visits. New-action order is a deterministic SHA-256 rank of stage seed, exact node fingerprint, and policy action ID.

Rollouts use per-seed MAST only. The first 1,000 simulations choose uniformly; afterward epsilon is 0.20 and exploitation requires four visits for the `active_character_id + policy_action_id` context. MAST begins empty and is updated only by completed rollouts from the current stage. PCG64 generator state and all MAST counts/value sums are checkpointed exactly.

## Compact tree and exact reconstruction

The tree is held in fixed-capacity typed NumPy arrays for parent, incoming slot, depth, visit/value statistics, legal/expanded masks, terminal/invalid flags, snapshot reference, damage, times, and 64-byte fingerprints. A fixed `(maximum_nodes, 25)` signed child table uses `-1` as its sentinel. No large Python state object is retained per node.

The root and depths divisible by eight have compact JSON snapshots. Other nodes restore the nearest snapshot ancestor and replay at most seven selected tree actions. Reconstruction verifies the full fingerprint, total damage, combat time, and current time. Snapshot JSON is zlib-compressed into an append-only file with an indexed, hashed committed prefix. Exact full-state payloads may share bytes, but node/edge visit statistics remain local. The decoded-state LRU is bounded to 128 entries and 512 MiB and is not checkpointed.

Search action execution uses the normal simulator mechanics with `record_diagnostics=False`, followed by cleanup selected exclusively from the shared `DIAGNOSTIC_ONLY_FIELDS` classification. It omits timeline rows, serialized action/damage/mechanic history, and debug snapshots while preserving the live `ActionResult`, selected/resolved action behavior, damage, clocks, resources, cooldowns, buffs, scheduled effects, mechanics, legal actions, and both search fingerprints. Final retained-route replay continues to use the normal full-diagnostic path. Full/light guards cover every legal action in representative zero-time swap, timed Intro/Aemeath Outro, scheduled Sigillum, Mornye field, Tune Break, and horizon states, plus deterministic short and 120-second rollouts.

## Memory, checkpoint, and calibration boundary

The single-process plan has a 22 GiB hard ceiling (`23622320128` bytes) and a 20 GiB soft target. Accounting includes every typed array, child/fingerprint storage, snapshot/index/cache bytes, MAST, retained routes, scratch space, serialization buffer, peak RSS, and a conservative estimate. The CLI may lower but never raise the hard limit; no page file is assumed.

Checkpoints atomically retain the latest and previous generations, including plan/stage hashes, tree and children, snapshot prefix/index, PCG64 state, MAST, completed routes, and counters. Resume validates every hash before any log, snapshot, or tree mutation. A missing/truncated latest atomic generation falls back explicitly to a fully validated previous generation; hash corruption never silently falls back. Deterministic logical hashes exclude wall-clock and RSS measurements.

Fresh production execution accepts only the plan's canonical output root and refuses a nonempty root. Resume requires a valid checkpoint, and the public CLI has no generic force/test bypass. Beam comparison reporting validates the compact result manifest against SHA-256 `247f2a912d05bd4d89a3a7bbcb16c0877515427a8b46f7dc1795501b255b03ef`; a missing or mismatched file disables only comparison and can never supply an overall winner.

## Pre-verification bounded-probe correction

The first candidate-117 implementation failed the real bounded 200-simulation probe because every MCTS reconstruction, expansion, and rollout action retained and repeatedly serialized the full reporting diagnostics. This was corrected before external verification. The corrected real seed-117001 `100 + resume to 200` probe completed all 200 rollouts in 39.3047 seconds locally, retained zero lightweight diagnostic rows/bytes, passed the former simulation-150 slowdown region through simulation 200, and left no worker process. Its two-run repeatability guard completed in 79.5023 seconds with identical logical, RNG, MAST, damage, selected-route, and resolved-route hashes. These are bounded validation probes, not the 20,000-simulation calibration.

The only planned real stage is `calibration_20k_seed_117001`: 20,000 simulations, seed 117001, 25,001 nodes, stride 8, checkpoint every 1,000 simulations, and a four-hour wall-clock ceiling. It is calibration only and was deliberately not executed in candidate 117. Production multi-seed stages require later review and a later plan.

## Future reviewed commands (documented, not executed)

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
$env:OMP_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"
$env:OPENBLAS_NUM_THREADS="1"
$env:NUMEXPR_NUM_THREADS="1"

.\.venv\Scripts\python.exe search\run_mcts.py `
  --plan data\mcts_plan_v117_32gb.json `
  --dry-run-plan

.\.venv\Scripts\python.exe search\run_mcts.py `
  --plan data\mcts_plan_v117_32gb.json `
  --execute `
  --only-stage calibration_20k_seed_117001 `
  --max-simulations 20000 `
  --output-root results\mcts_v117_32gb\calibration_20k_seed_117001

.\.venv\Scripts\python.exe search\run_mcts.py `
  --plan data\mcts_plan_v117_32gb.json `
  --execute `
  --resume `
  --only-stage calibration_20k_seed_117001 `
  --max-simulations 20000 `
  --output-root results\mcts_v117_32gb\calibration_20k_seed_117001
```
