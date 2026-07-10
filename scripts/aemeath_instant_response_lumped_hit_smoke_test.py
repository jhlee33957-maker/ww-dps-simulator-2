from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.action_executor import execute_action
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def assert_close(actual: float, expected: float, label: str) -> None:
    assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), f"{label}: {actual} != {expected}"


def configure_instant_response(sim: Simulation, *, form: str, enabled: bool) -> None:
    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = form
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = 20.0
    data["resonance_rate"] = 4.0
    data["instant_response"] = enabled
    data["instant_response_consumed"] = False


def direct_result(action_id: str, *, form: str, instant_response: bool):
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    configure_instant_response(sim, form=form, enabled=instant_response)
    return execute_action(
        sim.actions[action_id],
        sim.state,
        sim.characters,
        sim.buffs,
        mechanic=sim.character_mechanics["aemeath"],
        combat_duration=sim.combat_duration,
        weapon_definitions=sim.weapon_definitions,
    )


def routed_entry(*, form: str):
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    configure_instant_response(sim, form=form, enabled=True)
    assert sim.execute_action("aemeath_heavy_attack")
    return sim.timeline[-1]


def assert_lumped_instant_response_action(
    *,
    action_id: str,
    form: str,
    expected_action_time: float,
) -> None:
    normal = direct_result(action_id, form=form, instant_response=False)
    instant = routed_entry(form=form)

    assert instant.resolved_action_id == action_id
    assert_close(instant.action_time, expected_action_time, f"{action_id} Instant Response action_time")
    assert instant.damage > 0.0
    assert instant.hit_details
    assert instant.hit_count == 1
    assert len(instant.hit_details) == 1
    assert instant.hit_details[0]["hit_time"] <= instant.action_time
    assert_close(instant.hit_details[0]["hit_time"], instant.action_time, f"{action_id} effective hit_time")

    assert normal.hit_details
    assert len(normal.hit_details) == 1
    assert_close(
        instant.hit_details[0]["damage_multiplier"],
        normal.hit_details[0]["damage_multiplier"],
        f"{action_id} source coefficient",
    )


def main() -> None:
    assert_lumped_instant_response_action(
        action_id="aemeath_heavy_aemeath_charged_2",
        form="aemeath",
        expected_action_time=91 / 60,
    )
    assert_lumped_instant_response_action(
        action_id="aemeath_heavy_mech_charged_2",
        form="mech",
        expected_action_time=56 / 60,
    )


if __name__ == "__main__":
    main()
