# Candidate 118: reviewed candidate-117 MCTS calibration

Candidate 118 ingests the externally reviewed `calibration_20k_seed_117001` output as a calibration result. The raw output remains preserved locally and unchanged. This is not a final MCTS result and does not prove a global or local optimum.

## Integrity and result

- Review ZIP SHA-256: `71af1ed95f574c4fc28284e3b77f8bf944828571d1dd3bce3a7dc746a2c78fb3` (74 entries; CRC clean)
- Full raw inventory: 111 files, 38,944,560 bytes
- Normalized entry digest: `b959d86ca0e4657e6dd918340eef87a520b02ea158bb30f661928f81b204e0b7`
- Simulations/completed/invalid: 20,000 / 20,000 / 0
- Nodes and retained completed routes: 20,001 and 128
- Winner: `5aab329ce5b526a7`, 4,128,137.812582737 damage, 34,401.14843818948 DPS
- Selected SHA-256: `5aab329ce5b526a709d530ae0a3037d4e8e776dff7726bfa0ecc4b02ca83116c`
- Resolved SHA-256: `bccd12d7c852d65e168e4ead82fd6fb2514d4d856e865db41a74620699316e1d`
- Replay: 180 selected/resolved/executed actions; all available and executed; final combat time 120.0

The best-damage checkpoints were 2,923,979.8335301215 at 1k; 3,184,203.7336018938 at 2k; 3,498,929.9226562413 at 3k; 3,764,027.8197907014 at 4k; 3,916,158.19797584 at 5k; 4,123,783.6584580713 at 8k; and 4,128,137.812582737 at 12k and 20k. The winner was first found at simulation 11,561, followed by 8,439 simulations without improvement. This plateau is an observation only.

## Interpretation

The calibration is 1,523,754.4619702548 damage (26.960076164770296%) below the completed Beam winner and 1,148,706.546109307 damage (21.76881613377799%) below the best trained model. Beam route `67a4250b3b8d0de9` remains the overall project winner.

Candidate 117's historical phase fields overlap: selection included expansion. Without rewriting the reviewed raw result, candidate 118 derives exclusive selection as 63.89053058042191 seconds. The exclusive phase sum is 3334.8130768793635 seconds and other overhead is 3.3619934206362814 seconds within 3338.1750703 elapsed seconds. Future runner timers are mutually exclusive.

## Candidate-118 production plan

`data/mcts_plan_v118_32gb_3x50k.json` defines three independent empty-tree, empty-MAST seeds: 118001, 118002, and 118003. Each stage has 50,000 simulations, 60,001 nodes, a 120-second horizon, 1,000-simulation checkpoints, a 23,622,320,128-byte hard budget, and rolling latest-plus-previous checkpoint retention. It imports no calibration, Beam, manual, BC, PPO, tree, MAST, route, or probability guidance. Production was not executed.

After candidate 118 is externally verified, execute one stage at a time (remove `--resume` for a fresh run):

```powershell
.\.venv\Scripts\python.exe search\run_mcts.py `
  --plan data\mcts_plan_v118_32gb_3x50k.json `
  --execute `
  --only-stage production_50k_seed_118001 `
  --max-simulations 50000 `
  --output-root results\mcts_v118_32gb\production_50k_seed_118001
```

Use the corresponding stage and root for seeds 118002 and 118003. To resume a stage, add `--resume` without changing its stage or root. Do not create a 100k/200k extension until all three 50k results are externally reviewed.

The optional cleanup tool defaults to dry-run. It may remove only obsolete raw checkpoint-generation payloads and requires a valid candidate-118 archive before `--apply`; candidate implementation did not apply cleanup.
