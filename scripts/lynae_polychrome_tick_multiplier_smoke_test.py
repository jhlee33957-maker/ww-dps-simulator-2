from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def hit_sum(action: dict) -> float:
    return round(sum(float(hit.get("damage_multiplier") or 0.0) for hit in action.get("hits", [])), 10)


def main() -> None:
    actions = {item["id"]: item for item in json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))}

    stage_2 = actions["lynae_polychrome_leap_stage_2"]
    assert len(stage_2["hits"]) == 1
    assert abs(stage_2["hits"][0]["damage_multiplier"] - 1.0140) < 1e-9
    assert abs(hit_sum(stage_2) - 1.0140) < 1e-9
    assert abs(stage_2["damage_multiplier"] - 1.0140) < 1e-9

    stage_3 = actions["lynae_polychrome_leap_stage_3"]
    assert len(stage_3["hits"]) == 1
    assert abs(stage_3["hits"][0]["damage_multiplier"] - 0.6550) < 1e-9
    assert abs(hit_sum(stage_3) - 0.6550) < 1e-9
    assert abs(stage_3["damage_multiplier"] - 0.6550) < 1e-9

    assert abs(actions["lynae_polychrome_leap_stage_2_c1"]["damage_multiplier"] - 2.2308) < 1e-9
    assert abs(actions["lynae_polychrome_leap_stage_3_c1"]["damage_multiplier"] - 1.4410) < 1e-9
    print("lynae_polychrome_tick_multiplier_smoke_test ok")


if __name__ == "__main__":
    main()
