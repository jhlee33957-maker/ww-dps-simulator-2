from __future__ import annotations

import time
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from scripts.guarded_ppo_state_integrity_smoke_test import run_state_integrity_contract

    elapsed: list[float] = []
    for _ in range(5):
        started = time.perf_counter()
        run_state_integrity_contract()
        elapsed.append(time.perf_counter() - started)
    assert max(elapsed) < 30.0, elapsed
    print(f"guarded_ppo_state_integrity_repeatability_smoke_test ok: timings={[round(value, 6) for value in elapsed]}")


if __name__ == "__main__":
    main()
