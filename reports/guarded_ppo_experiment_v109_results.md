# Guarded PPO v109 Completed Experiment Results

Candidate 110 ingests the externally reviewed completed v109 guarded PPO experiment. Candidate 110 remains pending external review.

## Winner

- Winner: `verified_bc_model`
- Model: `models/maskable_ppo_bc_v105.zip`
- Total damage: `5165134.682363356`
- DPS: `43042.78901969464`
- Global optimum proven: `false`

## Timestep Budget

- Requested aggregate timesteps: `300000`
- Actual aggregate SB3 model timesteps: `307200`
- Rollout granularity: `512`
- Per-branch overshoot: `2400` (`0.024`)

## Branch Results

| Branch | Best requested step | Best damage | Best / BC | Final requested step | Final damage | Final / BC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bc_conservative_seed_11` | 10000 | 5165134.682363356 | 1.0 | 100000 | 5134470.883053988 | 0.9940633107953465 |
| `bc_exploratory_seed_73` | 10000 | 5165134.682363356 | 1.0 | 100000 | 4777468.267968915 | 0.9249455361312939 |
| `scratch_control_seed_137` | 50000 | 2566933.375001255 | 0.49697317356819243 | 100000 | 1816940.651360404 | 0.3517702370016508 |

## Interpretation

The completed guarded PPO budget found no checkpoint above the verified BC/manual result. The scratch control remains far below BC under this budget. This is useful negative evidence for this PPO configuration, not a proof of global optimality.

Route similarity remains diagnostic only and is not part of winner selection.
