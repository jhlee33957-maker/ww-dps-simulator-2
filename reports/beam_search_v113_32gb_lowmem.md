# Candidate 113: 32 GB low-memory Beam Search

Candidate 113 is an infrastructure-only, externally unreviewed candidate. It does not contain a 3M/5M Beam result, an MCTS result, or new BC/PPO training. The verified 120-second BC result remains the incumbent at `5,165,134.682363356` total damage (`43,042.78901969464` DPS). No global optimum is claimed.

## Why a separate configuration is required

The v111 full stage uses width 4096 and has a conservative estimate of roughly 40.6 GiB. That configuration is unsafe on a 32 GB Windows machine. The new stage reserves at least 8 GB for Windows and supporting processes and sets a hard 22 GiB (`23,622,320,128` byte) Beam-process limit. It uses a separate plan and output root and explicitly refuses the abandoned `results/beam_search_v111_full_120s` output.

The reviewed low-memory stage keeps the deterministic, exact, order-independent retention contract but narrows the Beam to width 1792, split into damage/diversity quotas of 896/896. Each destination bucket can represent 16,384 unique fingerprints while only 4,096 candidates remain in memory before deterministic compressed spill. Atomic checkpoints, compact manifests, route-store compaction, and partial-node action cursors make budget interruption resumable without changing arrival-order-independent selection.

The narrower Beam trades search coverage for safety. A failure to beat the incumbent is therefore weaker negative evidence than the width-4096 plan would provide. MCTS can later provide an independent complementary search, but it is deliberately outside candidate 113.

Plan: `data/beam_search_plan_v113_32gb.json`  
Plan SHA-256: `ffd9ce47ec9b92b2c4b59f295d50d0ce5204fcba577af0f78b9fa917b19b291d`  
Canonical output: `results/beam_search_v113_lowmem_32gb`

## Slim runtime workspace

The builder copies the runtime into a new directory and never slims the verified source tree in place. It retains code, canonical data, manifests, compact result summaries, reports, progress metadata, and post-run archive/guard scripts. It omits `.git`, `.venv`, caches, project/model ZIPs, historical model/checkpoint bytes, the abandoned 64 GB output, and unneeded historical frontiers, accumulators, logs, and timelines. Their project-relative paths, sizes, hashes, and reasons are recorded in `LOWMEM_WORKSPACE_MANIFEST.json`; the generation timestamp is isolated in `LOWMEM_WORKSPACE_BUILD_RECEIPT.json`. Full audit artifacts remain preserved in the externally verified candidate-112 archive (`b602af3cd1b87cac1529baa23042e023ce2c90e9d1560426567943da95515fc5`).

```powershell
.\.venv\Scripts\python.exe scripts\build_lowmem_beam_workspace.py `
  --source . `
  --output "..\ww-dps-simulator-2-113-lowmem" `
  --apply
```

The slim copy intentionally excludes `.venv`. Create a compatible virtual environment in the new workspace (or invoke a known-compatible Python interpreter) and install the project dependencies before running its checks.

After a future reviewed run, `scripts/build_lowmem_beam_result_archive.py --workspace . --output ..\ww-dps-simulator-2-113-lowmem-result.zip` creates a cache-free post-run archive without requiring the omitted historical model checkpoints.

```powershell
cd ..\ww-dps-simulator-2-113-lowmem

.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v113_32gb.json `
  --dry-run-plan
```

## Reviewed future execution sequence

The plan maximum is 5,000,000 expansions, but the first execution is capped at 3,000,000. Review memory, runtime, and any completed 120-second result before extending the same output to 5M.

First 3M execution, only after candidate 113 external verification:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v113_32gb.json `
  --execute `
  --only-stage full_120s_lowmem_32gb `
  --max-expansions 3000000 `
  --output-root results\beam_search_v113_lowmem_32gb
```

Resume an interrupted 3M run:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v113_32gb.json `
  --execute `
  --resume `
  --only-stage full_120s_lowmem_32gb `
  --max-expansions 3000000 `
  --output-root results\beam_search_v113_lowmem_32gb
```

Extend only after reviewing the 3M result:

```powershell
.\.venv\Scripts\python.exe search\run_beam_search.py `
  --plan data\beam_search_plan_v113_32gb.json `
  --execute `
  --resume `
  --only-stage full_120s_lowmem_32gb `
  --max-expansions 5000000 `
  --output-root results\beam_search_v113_lowmem_32gb
```

Winner selection remains deterministic completed 120-second total damage only. Route similarity is diagnostic only; manual-route and BC/PPO policy guidance remain disabled.

## Bounded validation probe

The original candidate-113 26.4851-second probe claim was withdrawn after external review found that the monolithic v111 gzip JSON spill could stall in a fresh Linux/Python 3.13 extraction. The corrected low-memory runtime uses `beam_search_accumulator_chunk_jsonl_gzip_v113`: a deterministic gzip JSON-lines stream with an association header followed by one incrementally encoded node per record. Writes are atomic, compressed-file hashing is streamed, reads validate and iterate line by line, and legacy v111 chunks retain backward-compatible reading.

The corrected Windows probe retained the 120-second horizon and temporary 10,000-expansion cap. Search runtime was 23.4023 seconds, total process runtime was 26.8345 seconds, and throughput was 427.3085 expansions/s. Peak live nodes were 5,126, tracked memory was 262,070,492 bytes, and peak RSS was 612,466,688 bytes. Six spill chunks occupied 1,688,340 bytes compressed; the largest was 48,592,746 bytes uncompressed but peak serialization and restore buffers were only 24,273 bytes. The peak finalization unique set estimate was 46,223,513 bytes, the final sort list was 19,344 bytes, the compact manifest was 1,419,069 bytes, and checkpoint count was 2.

Two isolated Windows process-group runs exited normally in 28.4276 and 31.9241 seconds with identical deterministic result hash `88f09ecbc2b507a8fd7813afbf91d7a549cab8975b0b447b4422f660198db7b1`, identical spill bytes/counts, no surviving child, no cache creation, and no canonical-result mutation. Corrected POSIX packaged metrics remain pending fresh-extraction validation; candidate 113 remains pending external review and is not authorized for the 3M run on the basis of Windows results alone.
