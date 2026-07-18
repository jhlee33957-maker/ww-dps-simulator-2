from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_v121_runtime_test_utils import make_account_sim, ready_aemeath_charged_ii


def main() -> None:
    sim = make_account_sim("aemeath", aemeath_resonance_mode="fusion_burst")
    ready_aemeath_charged_ii(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    ready_aemeath_charged_ii(sim)
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    events = [event for event in sim.state.character_mechanics_state["aemeath"]["fusion_trail_event_log"] if event["event_type"] == "fusion_effect_application"]
    assert len(events) == 2
    assert all(event["cooldown_seconds"] == 0.0 for event in events)
    assert all(event["cooldown_source_ref"] == "base!FG73 / base!FP73" for event in events)
    print("aemeath_s3_fusion_heavy_source_cooldown_v121_smoke_test ok")


if __name__ == "__main__":
    main()
