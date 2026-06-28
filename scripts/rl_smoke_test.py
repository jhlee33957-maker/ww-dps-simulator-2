from __future__ import annotations

from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from sb3_contrib import MaskablePPO  # noqa: F401
    from env.wuwa_env import WuwaDpsEnv
except ModuleNotFoundError:
    print("Missing RL dependency. Run: pip install -r requirements.txt")
    raise SystemExit(0) from None


def main() -> None:
    env = WuwaDpsEnv(PROJECT_ROOT / "data")
    observation, _ = env.reset()
    print("Observation shape:", observation.shape)
    print("Initial action mask:", env.action_masks().astype(int).tolist())

    rng = random.Random(42)
    for step_index in range(8):
        mask = env.action_masks()
        valid_indexes = [index for index, valid in enumerate(mask) if valid]
        if not valid_indexes:
            print("No valid actions remain.")
            break
        action_index = rng.choice(valid_indexes)
        observation, reward, terminated, truncated, info = env.step(action_index)
        print(
            f"Step {step_index + 1}: action={info['action_id']} "
            f"reward={reward:.4f} terminated={terminated} truncated={truncated} "
            f"time={env.simulation.state.current_time:.2f} "
            f"damage={env.simulation.state.total_damage:.2f}"
        )
        if terminated or truncated:
            break


if __name__ == "__main__":
    main()
