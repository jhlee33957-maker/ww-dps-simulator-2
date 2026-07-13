# Guarded PPO Experiment v109

Candidate 109 adds reviewable infrastructure for a guarded multi-branch PPO continuation experiment. It does not execute the long PPO budget.

## Objective

- Compare policies by deterministic 120-second total damage only.
- Do not claim a global optimum.
- Do not use route-similarity rewards, character usage rewards, BC refresh, early stopping, or rollback.
- Keep the externally verified BC model as the initial global best until a deterministic evaluation beats it by more than `1e-6` damage.

## Branches

| Branch | Initialization | Seed | Timesteps | Chunk | Learning rate | Entropy |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `bc_conservative_seed_11` | `models/maskable_ppo_bc_v105.zip` | 11 | 100000 | 10000 | 0.0001 | 0.005 |
| `bc_exploratory_seed_73` | `models/maskable_ppo_bc_v105.zip` | 73 | 100000 | 10000 | 0.0003 | 0.02 |
| `scratch_control_seed_137` | scratch | 137 | 100000 | 10000 | 0.0003 | 0.02 |

All branches use `n_steps=512`, `batch_size=64`, `gamma=0.999`, party `aemeath_mornye_lynae_enabled_test_party`, initial active character `aemeath`, and reset mode `none`.
Loaded-model branches re-seed the loaded `MaskablePPO` object, environment, and RNGs with the effective chunk seed. The deterministic seed rule is `branch_base_seed + chunk_index - 1`.

## Guardrails

- Checkpoints are immutable: `models/guarded_ppo_v109/<branch>/step_XXXXXXXXX.zip`.
- Each branch resumes from its own latest checkpoint, never from global best by default.
- Global best is retained as metadata in `best_checkpoint.json`; there is no `best.zip`.
- Incumbents are normalized into the state and leaderboard before any PPO chunk: manual baseline, verified BC, prior 100k PPO, and step-0 verified BC aliases for BC-initialized branches.
- Tie handling uses absolute tolerance `1e-6` and prefers externally verified immutable incumbents, then earlier declared/evaluated records.
- Experiment state, leaderboard, best manifest, and chunk records are written atomically. Resume verifies checkpoint, sidecar, summary, and timeline hashes before continuing.
- Initial experiment state is written before step-0 BC alias evaluation. The two BC warm-start branches share one deterministic verified-BC step-0 evaluation artifact, recorded as explicit aliases.
- Resume adopts a valid checkpoint/sidecar pair left behind after a parent-process crash between model save and state update; ambiguous partial orphan artifacts fail instead of being overwritten.
- Training and evaluation subprocesses use explicit timeouts, process-tree termination on timeout, and stage-specific stdout/stderr log files with SHA-256s in state records.
- Guarded archive validation runs one bounded PPO training lifecycle in fresh extraction; crash/resume, state-integrity, route-diagnostic, and timeout cases are covered by lightweight focused guards.
- Every PPO checkpoint receives a model-specific `.ppo_metadata.json` sidecar with model hash, parent hash, branch/chunk identity, PPO hyperparameters, active contracts, reward flags, and experiment-plan hash.
- Evaluation prefers `.ppo_metadata.json`, then `.bc_metadata.json`, then only a matching legacy global metadata file.

## Plan Hash

`data/guarded_ppo_experiment_plan_v109.json`

SHA-256: `0306c734347e49460fd7273bce546eed80a2db657e460eb707f5cab961a9e0e6`

## Execution

Dry-run review:

```powershell
.\.venv\Scripts\python.exe rl\run_guarded_ppo_experiment.py --dry-run-plan --plan data\guarded_ppo_experiment_plan_v109.json
```

After review, execute:

```powershell
.\.venv\Scripts\python.exe rl\run_guarded_ppo_experiment.py --execute --plan data\guarded_ppo_experiment_plan_v109.json
```

Resume an interrupted run:

```powershell
.\.venv\Scripts\python.exe rl\run_guarded_ppo_experiment.py --execute --resume --plan data\guarded_ppo_experiment_plan_v109.json
```

Resume or run one branch with an explicit chunk cap:

```powershell
.\.venv\Scripts\python.exe rl\run_guarded_ppo_experiment.py --execute --resume --only-branch bc_conservative_seed_11 --max-chunks 1 --plan data\guarded_ppo_experiment_plan_v109.json
```

Bounded infrastructure smoke:

```powershell
.\.venv\Scripts\python.exe rl\run_guarded_ppo_experiment.py --execute --smoke-run --output-root $env:TEMP\guarded-ppo-v109-smoke --plan data\guarded_ppo_experiment_plan_v109.json
```

Running `rl\run_guarded_ppo_experiment.py` with no mode flag exits with help/error and does not train. `--resume` requires `--execute`; `--smoke-run` is explicit and rejected if pointed at canonical project output paths.
