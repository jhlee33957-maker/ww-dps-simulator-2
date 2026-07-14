# Candidate 115 review of the v114 3M Beam checkpoint

The checkpoint is healthy and resumable, but it is not a completed 120-second result. It stopped at exactly 3,000,000 expansions with `expansion_budget_exhausted`, zero completed routes, 135 completed half-second buckets, and pending buckets 134-137.

The best partial node reached 67.48333333333329 combat seconds and 2,850,679.8061139295 damage in 92 actions. It is diagnostic only: it is neither a winner nor a final DPS result. The old `final_summary.json`, `leaderboard.json`, `best_route.json`, and `execution_result.json` contain the legacy v114 full-stage misclassification and are not authoritative for project-winner reporting; the search state remains valid.

The current project winner remains the reviewed v114 guarded-PPO 90k evaluation at 5,276,844.358692044 damage (43,973.70298910037 DPS). The explicit corrected scope is `completed_120s_project_comparison`, so an expansion-budget checkpoint with no completed Beam routes retains that incumbent and excludes partial nodes.

At 334.9876393772433 expansions/second, the run used 8,955.554317099974 seconds, peaked at 1,914,478,592 RSS bytes against a 23,622,320,128-byte budget, and wrote 31 checkpoints with the next at 3,100,000. It recorded 516,112 deduplicated states, 1,840,989 pruned states, and 402,052 zero-time expansions. The spill contract is `streaming_jsonl_gzip_v113` with chunk schema `beam_search_accumulator_chunk_jsonl_gzip_v113`.

The empirical recent-bucket rate projects the first 120-second completion around 5.5M-5.8M expansions, making the old 5M ceiling likely insufficient. Candidate 115 therefore reviews a 6.5M resume target. This is an execution-budget estimate, not a global-optimum claim.

The corrected candidate integrates one shared, read-only extension preflight into both the validator CLI and the real runner. It validates the exact source state and plan, canonical output root, referenced spill files, all 649 reviewed inventory entries, and the non-null best-partial metrics before any search-output mutation. The low-memory safety gate is capability-driven, so the 23,622,320,128-byte hard ceiling and canonical resume root remain mandatory even if a fixture renames the plan schema or stage.

The compact audit artifacts are `results/beam_search_v114_3m_reviewed_file_inventory_v115.json` and `results/beam_search_v114_3m_resume_extension_v115_receipt.json`. The source state hash remained `f1ac52b960465a7ea71ea8495b1c1f2d89a79766d5cdf2f6ad3e4872d2e25630` before and after validation.

The 1.75+ GiB checkpoint stays in `results/beam_search_v114_lowmem_32gb`, is excluded from the source archive, and must be preserved locally. Candidate 115 did not execute the long resume.
