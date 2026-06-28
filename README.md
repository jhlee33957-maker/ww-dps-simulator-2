# Wuwa DPS RL Simulator Prototype

This project is an initial scaffold for a Wuthering Waves-style DPS simulation tool. It is designed as a clean foundation for future reinforcement-learning experiments, not as a full game-accurate simulator.

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
- Concerto energy is tracked, but intro and outro logic is not implemented yet.
- Echo skill is modeled per character with a normal cooldown.
- No dash, animation canceling, hit timing, enemy behavior, or RL training is included yet.

## RL Status

The project has a Gymnasium-ready environment skeleton and an `action_masks()` method for future sb3-contrib Maskable PPO support. It does not implement training yet.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Smoke Test

```bash
python scripts/smoke_test.py
```

## Project Layout

- `app.py`: Streamlit prototype UI.
- `data/`: Dummy JSON data for characters, actions, and buffs.
- `simulator/`: Core deterministic simulation logic.
- `env/`: Gymnasium-ready environment skeleton for future RL.
- `scripts/`: Small local utility scripts such as the smoke test.
- `results/`: Placeholder for experiment outputs.
- `models/`: Placeholder for trained models later.

## Roadmap

1. Add hit timing.
2. Add real character data.
3. Add proper intro, outro, and concerto logic.
4. Add Beam Search baseline.
5. Add Maskable PPO training.
