from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import aemeath_s4_apply_party_bonus


def main() -> None:
    state = {"aemeath": {"sequence": 6}}
    first = aemeath_s4_apply_party_bonus(state, now=10.0)
    second = aemeath_s4_apply_party_bonus(state, now=12.5)
    buff = state["aemeath"]["s4_party_bonus"]
    assert first["party_all_attribute_damage_bonus"] == 0.20
    assert second["stacks"] == 1
    assert buff["expires_at"] == 42.5
    assert buff["value"] == 0.20
    print("aemeath_s4_party_bonus_v121_smoke_test ok")


if __name__ == "__main__":
    main()
