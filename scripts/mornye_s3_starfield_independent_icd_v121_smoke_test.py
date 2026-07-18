from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import mornye_s3_same_action_with_starfield


def main() -> None:
    state = {"mornye": {"sequence": 3}}
    first = mornye_s3_same_action_with_starfield(state, now=0.0)
    assert first["concerto_gain_total"] == 41.0
    assert first["relative_momentum_gain_total"] == 100.0
    blocked = mornye_s3_same_action_with_starfield(state, now=19.9)
    assert blocked["concerto_gain_total"] == 0.0
    starfield_only = mornye_s3_same_action_with_starfield(state, now=20.0)
    assert starfield_only["distributed_array"]["triggered"] is False
    assert starfield_only["starfield_r5"]["triggered"] is True
    assert starfield_only["concerto_gain_total"] == 16.0
    print("mornye_s3_starfield_independent_icd_v121_smoke_test ok")


if __name__ == "__main__":
    main()
