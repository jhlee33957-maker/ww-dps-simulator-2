# Wuwa DPS RL Simulator Prototype

This project is a Wuthering Waves-style DPS simulation tool focused on Maskable PPO reinforcement learning. It combines a deterministic simulator core, a Gymnasium environment with action masks, reusable damage formulas, training and evaluation scripts, and a Streamlit UI for deterministic validation and saved-model evaluation. It is still a prototype and uses dummy data rather than real game values.

## Current Scope

- Deterministic 120-second combat simulation.
- Time advances by action duration, not by fixed frames or ticks.
- The player or agent chooses a new action only after the current action finishes.
- If an action starts before 120.0 seconds, its full damage counts even if it ends after 120.0.
- Final DPS is always total_damage / 120.0.
- Gymnasium environment for Maskable PPO training.
- Streamlit UI with Demo Sequence and PPO Model evaluation modes.
- Dummy character, action, enemy, and buff data are included. No real game data is used.

## Character Mechanics Architecture

The common combat engine handles shared systems: damage formulas, action_time, hit timing, buffs, cooldowns, resources, attribute anomaly state, Havoc Bane DEF reduction, and the PPO reward objective. Character-specific mechanics are isolated under characters/ so the simulator core does not need character-specific branches.

Character mechanic modules can:

- initialize character-specific state
- resolve high-level actions into concrete actions
- add character-specific action availability rules
- advance character-specific timers whenever combat time passes
- update state before and after actions
- extend PPO observations
- provide debug state for Streamlit and smoke tests

Existing dummy characters use DefaultCharacterMechanic, which is a no-op. AemeathMechanic contains the first Aemeath-lite implementation. It resolves high-level policy actions into concrete internal actions and owns Aemeath-specific state updates. Full real-game Aemeath logic is planned later.

## Aemeath-lite Character Mechanic

Aemeath-lite is a first-pass architecture validation character, not a final real-game implementation. Common combat systems remain in simulator/. Aemeath-specific form state, combo state, action replacement, Synchronization Rate, Resonance Rate, Seraphic Duo, Overdrive, and Finale behavior live in characters/aemeath.py.

PPO and Demo Sequence select high-level actions such as aemeath_basic_attack, aemeath_resonance_skill, and aemeath_resonance_liberation. AemeathMechanic resolves those inputs into concrete internal actions such as Aemeath Form Basic Stage 1, Mech Basic Stage 2, Seraphic Duet, Overdrive, or Finale based on current Aemeath state. Concrete internal actions are hidden from PPO with policy_selectable = false.

Implemented Aemeath-lite scope:

- Aemeath Form and Mech Form
- Aemeath Form basic attack stages 1-4
- Mech Form basic attack stages 1-4
- Basic Attack resolution by current form and combo stage
- Resonance Skill replacement for form switch and Seraphic Duet
- Synchronization Rate and Resonance Rate
- Seraphic Duo duration state
- Resonance Liberation: Overdrive
- Heavenfall Edict: Finale
- Aemeath-specific PPO observation and Streamlit debug state

Not implemented yet:

- Starflux
- Tune Rupture
- Fusion Burst
- Fusion Trail
- Intro and Outro skills
- team-wide buffs
- full passive effects
- air attacks and dodge counter
- exact real hit timings or final damage values

All Aemeath-lite damage multipliers, action_time values, hit timings, and resource gains are placeholder/sample values for architecture testing.

Character mechanics have an advance_time hook that runs whenever combat time advances, even if the character is off-field. Aemeath Seraphic Duo uses this hook, so its remaining time decreases during swaps and during other characters' actions. Heavenfall Finale is separated from Overdrive cooldown by using its own cooldown group. Aemeath numerical values are still placeholder/sample values; real Aemeath skill coefficients are not implemented yet.

## Damage Formulas

The formula layer lives in simulator/damage_formula.py and currently supports normal damage, Tune Break damage, and simplified attribute anomaly tick damage.

Normal Damage =
Skill Multiplier x Base ATK x ATK Multiplier x DMG Bonus Multiplier x Expected Crit Multiplier x Boost Multiplier x RES Multiplier x DEF Multiplier x DMG Taken Multiplier x Final DMG Multiplier

Base ATK = Character Base ATK + Weapon Base ATK

ATK Multiplier = 1 + ATK% + Flat ATK / Base ATK

Expected Crit Multiplier = 1 + Crit Rate x (Crit DMG - 1)

Tune Break Damage =
Tune Break Base x Tune Break Multiplier x Tune Break Boost x RES Multiplier x DEF Multiplier x Tune DMG Bonus Multiplier

## Hit Timing Model

The simulator does not model animation playback time and does not include a general cancel system. For DPS and reinforcement learning, each action has:

- action_time: combat timer time consumed by the action and the time until the next action decision.
- hits: damage events that occur at offsets inside action_time.

Buffs, Havoc Bane, and other time-sensitive effects are evaluated at each hit time. For example, if Havoc Bane has 0.30 seconds remaining at action start, a hit at 0.20 receives its DEF reduction and a hit at 0.45 does not. Current hit timing data is dummy/sample data; real character-specific hit timings are not implemented yet.
## Attribute Anomaly System

- Actions apply anomaly stacks to enemy-wide CombatState.
- Active anomalies persist with simplified remaining_duration, tick_interval, and tick_timer values.
- Aero Erosion, Spectro Frazzle, and Electro Flare deal tick damage while active.
- Havoc Bane does not deal direct damage in this simplified implementation.
- Havoc Bane contributes defense reduction while active: def_reduction += stacks * 0.02.
- Anomalies applied by the current action start affecting and ticking on later actions, not the same action.
- Current durations, stack limits, tick intervals, and trigger behavior are simplified assumptions, not game-verified rules.

Supported anomaly types:

- aero_erosion
- spectro_frazzle
- electro_flare
- havoc_bane defense reduction

Monster-specific resistance data, character-specific special coefficients, hit timing, and full anomaly rules are not implemented yet. Current formulas are implemented as a reusable calculation layer with sample values.

## Simplified Rules

- Damage is split into normal_damage, tune_break_damage, anomaly_tick_damage, and total_action_damage in the timeline. Timeline rows also include action_time, hit_count, and hit_details for debugging.
- damage/anomaly_damage remain compatibility fields and mirror total_action_damage/anomaly_tick_damage where appropriate.
- Damage uses expected crit value instead of random crit rolls.
- Damage is calculated using buffs and anomalies that are already active at the start of an action. Buffs and anomalies applied by the current action are added after the action resolves and affect later actions only.
- Existing buffs, cooldowns, and active anomalies advance by the action duration.
- Cooldowns are set after the action resolves, so cooldown timing currently starts from the end of the action.
- Actions may define cooldown_group. When present, cooldown checking and cooldown storage use that group key instead of action.id. Existing actions without cooldown_group keep their original behavior.
- Actions may define policy_selectable = false to hide concrete internal mechanic actions from PPO while keeping them available for mechanic resolution.
- Actions may define mechanic_effects. The common simulator stores this data but does not interpret character-specific effect keys.
- Resonance energy is capped by each character's resonance_energy_max, currently 125.0 in sample data.
- Concerto energy is capped at 100.0.
- Wasted resonance and concerto energy are tracked per character and per timeline action.
- Swapping to the currently active character is invalid and appears invalid in action masks.

## Reinforcement Learning

Maskable PPO is implemented with sb3-contrib. It is used because many actions are invalid depending on active character, cooldowns, resonance energy, and swap state. The environment exposes action_masks(), and training/evaluation use those masks.

The RL reward is intentionally simple and objective:

```text
reward = damage_this_action / 10000.0
```

damage_this_action is the simulator total_action_damage for the selected action, including normal, Tune Break, and active anomaly tick components. Resource waste, buff usage, cooldown usage, and action counts are analysis metrics only. They are not reward terms. Training is done by script, not inside Streamlit. Streamlit only evaluates a saved model in PPO Model mode. Demo Sequence mode is for deterministic simulator validation.

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

The default model output is models/maskable_ppo_wuwa.zip. Training metadata is written to results/training_metadata.json.

## Evaluate PPO

```bash
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip
```

Evaluation writes results/ppo_evaluation_summary.json and results/ppo_timeline.csv.

## Run Streamlit

```bash
streamlit run app.py
```

Streamlit supports Demo Sequence and PPO Model modes. PPO Model mode loads and evaluates a saved model; it does not train.

## Checks

```bash
python -m compileall .
python scripts/smoke_test.py
python scripts/formula_smoke_test.py
python scripts/anomaly_smoke_test.py
python scripts/hit_timing_smoke_test.py
python scripts/mechanics_smoke_test.py
python scripts/aemeath_lite_smoke_test.py
python scripts/env_smoke_test.py
python scripts/rl_smoke_test.py
python rl/train_maskable_ppo.py --timesteps 50000
python rl/evaluate_maskable_ppo.py --model-path models/maskable_ppo_wuwa.zip
streamlit run app.py
```

## Project Layout

- app.py: Streamlit prototype UI with demo, anomaly notes, formula settings, and PPO model evaluation modes.
- characters/: Character mechanics plugin interface, default no-op mechanic, registry, and Aemeath-lite mechanic.
- data/: Dummy JSON data for characters, actions, enemy context, and buffs.
- simulator/: Core deterministic simulation logic, anomaly state system, and reusable damage formula layer.
- env/: Gymnasium environment, action masks, and objective damage reward.
- rl/: Maskable PPO training and evaluation scripts.
- scripts/: Smoke tests.
- results/: Training and evaluation artifacts.
- models/: Saved PPO models.

## Roadmap

1. Expand Aemeath-lite into fuller character-specific mechanics.
2. Add real character data.
3. Add monster-specific resistance and defense data.
4. Add proper intro, outro, concerto, and anomaly logic.
5. Tune Maskable PPO hyperparameters.
