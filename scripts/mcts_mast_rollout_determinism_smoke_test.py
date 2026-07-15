from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_search import MASTTable


def choices(seed: int) -> tuple[list[int], MASTTable]:
    rng = np.random.Generator(np.random.PCG64(seed)); table = MASTTable(("aemeath",), tuple(f"a{i}" for i in range(25)))
    assert not table.counts.any() and not table.value_sums.any()
    selected = [table.choose(active_character="aemeath", legal_slots=[0, 1, 2], simulation_index=i, rng=rng,
                             warmup=1000, epsilon=0.2, minimum_visits=4) for i in range(1001)]
    assert table.uniform_choices == 1000
    return selected, table


def main() -> None:
    a, ta = choices(117001); b, tb = choices(117001); c, _ = choices(117002)
    assert a == b and a != c and np.array_equal(ta.counts, tb.counts)
    ta.update([("aemeath", 1)] * 4, 0.8); assert ta.counts[0, 1] == 4 and ta.value_sums[0, 1] == 3.2
    assert not any(name in MASTTable.__init__.__code__.co_names for name in ("model", "route", "beam"))
    print("mcts_mast_rollout_determinism_smoke_test ok")


if __name__ == "__main__": main()
