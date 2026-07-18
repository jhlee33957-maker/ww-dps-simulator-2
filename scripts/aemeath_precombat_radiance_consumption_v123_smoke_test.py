from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import aemeath_state, enter_aemeath_from_lynae, make_account_sim


def main() -> None:
    simulation = make_account_sim()
    state = aemeath_state(simulation)
    assert simulation.execute_action("short_wait")
    assert state["account_radiance_quick_charge_ready"] is True
    assert simulation.execute_action("swap_to_lynae")
    assert state["account_radiance_quick_charge_ready"] is True

    simulation = make_account_sim()
    state = aemeath_state(simulation)
    assert simulation.execute_action("aemeath_heavy_attack") is False
    assert state["account_radiance_quick_charge_ready"] is True
    enter_aemeath_from_lynae(simulation)
    assert simulation.resolve_action_id("aemeath_heavy_attack") == "aemeath_heavy_aemeath_charged_2"
    assert state["account_radiance_quick_charge_ready"] is True
    assert simulation.execute_action("aemeath_heavy_attack")
    assert state["account_radiance_quick_charge_ready"] is False
    events = [
        event
        for event in simulation.state.character_mechanics_state["_account_constellation"]["events"]
        if event["event_type"] == "aemeath_s1_radiance_quick_charge_consumed"
    ]
    assert len(events) == 1
    assert events[0]["action_id"] == "aemeath_heavy_aemeath_charged_2"
    print("aemeath_precombat_radiance_consumption_v123_smoke_test ok")


if __name__ == "__main__":
    main()
