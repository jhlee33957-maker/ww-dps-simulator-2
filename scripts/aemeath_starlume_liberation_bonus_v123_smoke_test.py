from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import aemeath_state, enter_aemeath_from_lynae, make_account_sim


def execute_liberation(simulation) -> float:
    state = aemeath_state(simulation)
    before = float(state["resonance_rate"])
    assert "aemeath_resonance_liberation" in simulation.valid_action_ids()
    assert simulation.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"
    assert simulation.execute_action("aemeath_resonance_liberation")
    return float(state["resonance_rate"]) - before


def main() -> None:
    simulation = make_account_sim()
    enter_aemeath_from_lynae(simulation)
    state = aemeath_state(simulation)
    assert execute_liberation(simulation) == 2.0
    assert state["starlume_acceleration_remaining"] == 0.0

    illegal = make_account_sim()
    enter_aemeath_from_lynae(illegal)
    illegal.state.cooldowns["aemeath_overdrive"] = 1.0
    before = float(aemeath_state(illegal)["starlume_acceleration_remaining"])
    assert illegal.execute_action("aemeath_resonance_liberation") is False
    assert aemeath_state(illegal)["starlume_acceleration_remaining"] == before

    expired = make_account_sim()
    enter_aemeath_from_lynae(expired)
    aemeath_state(expired)["starlume_acceleration_remaining"] = 0.0
    assert execute_liberation(expired) == 1.0

    second = make_account_sim()
    enter_aemeath_from_lynae(second)
    assert execute_liberation(second) == 2.0
    state = aemeath_state(second)
    state["heavenfall_unbound"] = False
    state["heavenfall_unbound_remaining"] = 0.0
    second.state.cooldowns["aemeath_overdrive"] = 0.0
    second.state.resonance_energy["aemeath"] = 125.0
    state["resonance_rate"] = 0.0
    assert execute_liberation(second) == 1.0
    print("aemeath_starlume_liberation_bonus_v123_smoke_test ok")


if __name__ == "__main__":
    main()
