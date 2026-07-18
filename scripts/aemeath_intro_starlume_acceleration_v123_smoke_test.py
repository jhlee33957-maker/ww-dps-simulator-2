from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import aemeath_state, enter_aemeath_from_lynae, make_account_sim, set_concerto_ready


def main() -> None:
    generic = make_account_sim()
    assert generic.execute_action("swap_to_aemeath")
    assert aemeath_state(generic)["starlume_acceleration_remaining"] == 0.0

    failed = make_account_sim()
    failed.state.cooldowns["swap_reentry:aemeath"] = 1.0
    assert failed.execute_action("swap_to_aemeath") is False
    assert aemeath_state(failed)["starlume_acceleration_remaining"] == 0.0

    other_intro = make_account_sim()
    set_concerto_ready(other_intro, "mornye")
    assert other_intro.execute_action("swap_to_lynae")
    assert aemeath_state(other_intro)["starlume_acceleration_remaining"] == 0.0

    simulation = make_account_sim()
    row = enter_aemeath_from_lynae(simulation)
    state = aemeath_state(simulation)
    assert state["starlume_acceleration_remaining"] == 15.0
    event = next(event for event in row.transition_events if event.get("action_id") == "aemeath_qte_intro_human")
    assert event["starlume_acceleration_applied"] is True
    assert event["starlume_acceleration_remaining_after"] == 15.0
    assert simulation.execute_action("aemeath_basic_attack")
    assert 0.0 < state["starlume_acceleration_remaining"] < 15.0

    set_concerto_ready(simulation, "aemeath")
    assert simulation.execute_action("swap_to_lynae")
    set_concerto_ready(simulation, "lynae")
    assert simulation.execute_action("swap_to_aemeath")
    assert state["starlume_acceleration_remaining"] == 15.0
    print("aemeath_intro_starlume_acceleration_v123_smoke_test ok")


if __name__ == "__main__":
    main()
