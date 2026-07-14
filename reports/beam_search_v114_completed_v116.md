# Completed v114 Beam Search result (candidate 116 ingestion)

## Search validity

The reviewed search terminated naturally with `completed_search` at 4,908,270 expansions, before the 6,500,000 safety maximum. All 240 half-second buckets (0-239) are complete, no pending bucket or destination accumulator remains, and 128 unique completed 120-second routes were retained.

## Winning damage result

The overall project winner is Beam route `67a4250b3b8d0de9` at 5651892.274552992 total damage and 47099.1022879416 DPS. All 162 selected actions were available and executed during replay. The selected/resolved route hashes remain `67a4250b3b8d0de9cec625448756226106ef0ed5134b8c4e4a0378518fa2f434` and `2b594e575203f29293b1f0e57ae51a07ff85d535ac957bde38a5911f6858c43a`.

The best trained model remains `models/guarded_ppo_v109/bc_conservative_seed_11/step_000090000.zip` at 5276844.358692044 damage and 43973.70298910037 DPS. Beam improves by 375047.9158609472 damage (7.107428045384112%) and 3125.3992988412283 DPS.

## Non-global-optimum status

Winner selection is deterministic completed-120-second total damage only. Beam is the best reviewed project result, but pruning prevents this search from proving a global optimum.

## Corrected performance accounting

The resume invocation added 1,908,270 expansions in 7,659.986105200136 seconds, or 249.12186181441405 expansions/s. Cumulative elapsed time is 16,615.54042230011 seconds (approximately 4h 36m 55.54s), giving 295.40236882169023 cumulative expansions/s. The historical 640.7674808532514 value incorrectly divided cumulative expansions by resume-only elapsed time.

## Comparison references

The corrected winning-route summary labels the current manual v114 reference (5268418.084869607), the current reviewed model incumbent (5276844.358692044), and the historical verified BC reference (5165134.682363356) separately.

## Safe cleanup status

The full 1,051-file, 2,538,957,524-byte heavy result was validated before and after ingestion and was not modified. Cleanup was not applied. After candidate 116 passes external review, the dry-run cleanup tool may report 836 accumulator files (2,529,324,201 bytes) plus 207 redundant nested frontier files (3,838,673 bytes) as eligible, subject to all manifest/archive/replay guards.
