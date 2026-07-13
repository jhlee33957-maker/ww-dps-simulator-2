from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def hit_sum(action: dict) -> float:
    return round(sum(float(hit.get("damage_multiplier") or 0.0) for hit in action.get("hits", [])), 10)


def main() -> None:
    actions = {item["id"]: item for item in json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))}

    intro = actions["lynae_intro_time_to_show_some_colors"]
    assert len(intro["hits"]) == 1
    assert abs(intro["hits"][0]["damage_multiplier"] - 2.2480) < 1e-9
    assert abs(hit_sum(intro) - 2.2480) < 1e-9
    assert abs(intro["damage_multiplier"] - 2.2480) < 1e-9

    liberation = actions["lynae_resonance_liberation_prismatic_overblast"]
    assert len(liberation["hits"]) == 1
    assert abs(liberation["hits"][0]["damage_multiplier"] - 8.7480) < 1e-9
    assert abs(hit_sum(liberation) - 8.7480) < 1e-9

    vivid = actions["lynae_to_a_vivid_tomorrow"]
    assert len(vivid["hits"]) == 1
    assert abs(vivid["hits"][0]["damage_multiplier"] - 2.0106) < 1e-9
    assert abs(hit_sum(vivid) - 2.0106) < 1e-9
    assert abs(vivid["damage_multiplier"] - 2.0106) < 1e-9
    print("lynae_intro_liberation_vivid_tick_multiplier_smoke_test ok")


if __name__ == "__main__":
    main()
