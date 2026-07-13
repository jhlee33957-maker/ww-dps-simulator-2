from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    actions = {item["id"]: item for item in json.loads((ROOT / "data/actions.json").read_text(encoding="utf-8"))}
    action = actions["lynae_kaleidoscopic_basic_stage_5"]
    multipliers = [hit["damage_multiplier"] for hit in action["hits"]]
    assert multipliers == [2.5181]
    assert abs(sum(multipliers) - 2.5181) < 1e-9
    assert abs(action["damage_multiplier"] - 2.5181) < 1e-9
    assert action["metadata"]["repeated_tick_rows"][0]["max_hits"] == 5
    print("lynae_kp_stage5_tick_multiplier_smoke_test ok")


if __name__ == "__main__":
    main()
