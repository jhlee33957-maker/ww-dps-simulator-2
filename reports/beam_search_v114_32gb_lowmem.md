# Candidate 114: corrected 32 GB low-memory Beam Search

Candidate 114 remains pending external review. No 3M/5M Beam Search, MCTS, BC training, or PPO training was run, and no global optimum is claimed.

## Active plan and spill contract

- Plan: `data/beam_search_plan_v114_32gb.json`
- Plan SHA-256: `e70826d0040444f834398d55c922aacb4ee5b484bc6ef2e75ca5a0ad603bc18c`
- Stage: `full_120s_lowmem_32gb_v114`
- Canonical output: `results/beam_search_v114_lowmem_32gb`
- Explicit accumulator format: `streaming_jsonl_gzip_v113`
- Chunk schema: `beam_search_accumulator_chunk_jsonl_gzip_v113`

The active v114 stage now selects streaming spill through an explicit stage field. Legacy implicit selection remains available only for compatibility, and an unknown declaration is rejected. A focused real-stage test inserts more than 4,096 compact nodes and makes the generic legacy monolithic writer raise if invoked. The test passes streaming write/restore, association retention, reverse-order insertion, deterministic compressed hashes, partition merge, checkpoint/resume, and positive bounded buffer metrics.

## Corrected bounded probe

The 120-second-horizon probe was capped at 10,000 expansions. Its second isolated Windows run recorded 30.2822 seconds of search time, 33.5209 seconds total process time, 330.2272 expansions/s, and 395,329,536 bytes peak RSS. Six compressed spill chunks occupied 2,479,653 bytes (2,483,035-byte directory footprint). The largest uncompressed chunk was 55,600,032 bytes, while maximum serialization and restore buffers were both 24,532 bytes. The finalization unique-set estimate was 52,866,825 bytes and the final sort list was 22,208 bytes.

Two isolated process-group runs exited normally and completed cleanup. Search times were approximately 30.5355 and 30.2822 seconds, total process times 33.7867 and 33.5209 seconds, and peak RSS values 395,542,528 and 395,329,536 bytes. They produced the identical deterministic result SHA-256 `aa758e746344fbe685467540f16bdcc3c6899fdd6cb03e81ac881ce0440d92ef`, identical ordered spill-chunk hashes, the same best fingerprint and damage, no surviving child, no cache creation, and no canonical-output mutation.

The probe is bounded validation evidence only. It is not a completed 120-second route search and does not authorize resuming the incompatible v113 frontier.

## Future reviewed command

After external review, the first long run remains capped at 3,000,000 expansions:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v114_32gb.json `
  --execute `
  --only-stage full_120s_lowmem_32gb_v114 `
  --max-expansions 3000000 `
  --output-root results\beam_search_v114_lowmem_32gb
```

Only that v114 root may be resumed. The preserved v113 output is contract-incompatible with v114.
