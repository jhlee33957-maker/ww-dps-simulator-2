# Wuwa DPS RL Simulator Prototype

This project is a Wuthering Waves-style DPS simulation tool with deterministic simulation, a Beam Search baseline, and Maskable PPO reinforcement-learning training. It is still a prototype and uses dummy data rather than real game values.

## Current Scope

- Deterministic 120-second combat simulation.
- Time advances by action duration, not by fixed frames or ticks.
- The player or agent chooses a new action only after the current action finishes.
- If an action starts before `120.0` seconds, its full damage counts even if it ends after `120.0`.
- Final DPS is always `total_damage / 120.0`.
- Initial actions include Basic Attack, Resonance Skill, Resonance Liberation, Echo Skill, Swap Character, and Short Wait.
- Dummy character, action, and buff data are included. No real game data is used.

## Simplified Rules

- Damage uses expected crit value instead of random crit rolls.
- Damage is calculated using buffs that are already active at the start of an action. Buffs applied by the current action are added after the action resolves and affect later actions only.
- Existing buffs and cooldowns advance by the action duration.
- Cooldowns are set after the action resolves, so cooldown timing currently starts from the end of the action.
- Resonance energy is capped by each character's `resonance_energy_max`, currently `125.0` in sample data.
- Concerto energy is capped at `100.0`.
- Wasted resonance and concerto energy are tracked per character and per timeline action.
- Swapping to the currently active character is invalid and appears invalid in action masks.

## Reinforcement Learning

Maskable PPO is implemented with `sb3-contrib`. It is used because many actions are invalid depending on active character, cooldowns, resonance energy, and swap state. The environment exposes `action_masks()`, and training/evaluation use those masks.

The RL reward is intentionally simple and objective:

```text
reward = damage_this_action / 10000.0
```

Resource waste, buff usage, cooldown usage, and action counts are analysis metrics only. They are not reward terms. Training is done by script, not inside Streamlit. Streamlit only evaluates a saved model in PPO Model mode.

## Beam Search Baseline

Beam Search is a deterministic comparison baseline, not reinforcement learning. By default it searches valid actions only and scores candidates by total damage. It remains useful as a sanity check and comparison point for PPO results.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Train PPO

```bash
python rl/train_maskable_ppo.py --timesteps 50000
```

The default model output is `models/maskable_ppo_wuwa.zip`. Training metadata is written to `results/training_metadata.json`.

## Evaluate PPO

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip
```

Evaluation writes `results/ppo_evaluation_summary.json` and `results/ppo_timeline.csv`.

## Run Streamlit

```bash
streamlit run app.py
```

Streamlit supports Demo Sequence, Beam Search, and PPO Model modes. PPO Model mode loads and evaluates a saved model; it does not train.

## Checks

```bash
python -m compileall .
python scripts/smoke_test.py
python scripts/env_smoke_test.py
python scripts/beam_search_test.py
python scripts/rl_smoke_test.py
python rl/train_maskable_ppo.py --timesteps 50000
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip
streamlit run app.py
```

## Project Layout

- `app.py`: Streamlit prototype UI with demo, Beam Search, and PPO model evaluation modes.
- `data/`: Dummy JSON data for characters, actions, and buffs.
- `simulator/`: Core deterministic simulation logic.
- `env/`: Gymnasium environment and objective damage reward.
- `solver/`: Deterministic baselines such as Beam Search.
- `rl/`: Maskable PPO training and evaluation scripts.
- `scripts/`: Smoke tests.
- `results/`: Training and evaluation artifacts.
- `models/`: Saved PPO models.

## Roadmap

1. Add hit timing.
2. Add real character data.
3. Add proper intro, outro, and concerto logic.
4. Improve evaluation dashboards and comparison reports.
5. Tune Maskable PPO hyperparameters.
