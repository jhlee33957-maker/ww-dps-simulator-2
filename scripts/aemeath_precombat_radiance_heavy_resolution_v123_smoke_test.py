from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import aemeath_state, enter_aemeath_from_lynae, make_account_sim


def main() -> None:
    exact = make_account_sim(precombat_elapsed_seconds=4.0)
    assert aemeath_state(exact)["account_radiance_quick_charge_ready"] is False

    simulation = make_account_sim()
    state = aemeath_state(simulation)
    assert state["account_radiance_quick_charge_ready"] is True
    assert "aemeath_heavy_attack" not in simulation.valid_action_ids()
    assert state["account_radiance_quick_charge_ready"] is True

    enter_aemeath_from_lynae(simulation)
    assert "aemeath_heavy_attack" in simulation.valid_action_ids()
    assert simulation.resolve_action_id("aemeath_heavy_attack") == "aemeath_heavy_aemeath_charged_2"
    assert state["account_radiance_quick_charge_ready"] is True
    assert simulation.execute_action("aemeath_heavy_attack")
    assert simulation.timeline[-1].resolved_action_id == "aemeath_heavy_aemeath_charged_2"
    assert state["account_radiance_quick_charge_ready"] is False
    assert simulation.resolve_action_id("aemeath_heavy_attack") == "aemeath_heavy_aemeath_charged_1"
    print("aemeath_precombat_radiance_heavy_resolution_v123_smoke_test ok")


if __name__ == "__main__":
    main()
