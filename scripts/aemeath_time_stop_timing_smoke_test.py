from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.models import ActionData
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def approx(actual: float, expected: float, tolerance: float = 1e-4) -> bool:
    return math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)


def actions_by_id() -> dict[str, dict]:
    actions = json.loads((DATA_DIR / "actions.json").read_text(encoding="utf-8-sig"))
    return {action["id"]: action for action in actions}


def assert_time(action: dict, action_time: float, combat_time_cost: float) -> None:
    assert approx(action["action_time"], action_time), (
        f"{action['id']} action_time expected {action_time}, got {action['action_time']}"
    )
    assert approx(action["combat_time_cost"], combat_time_cost), (
        f"{action['id']} combat_time_cost expected {combat_time_cost}, got {action['combat_time_cost']}"
    )


def assert_has_damage_payload(action: dict) -> None:
    hits = action.get("hits", [])
    assert hits, f"{action['id']} should keep its hit payload"
    assert any(hit.get("damage_multiplier", 0) > 0 for hit in hits), (
        f"{action['id']} should keep damage multipliers"
    )


def test_whitelist_action_data() -> str:
    actions = actions_by_id()
    seraphic_id = (
        "aemeath_seraphic_duet_overture"
        if "aemeath_seraphic_duet_overture" in actions
        else "aemeath_seraphic_duet_overturn"
    )

    expected = {
        "aemeath_liberation_overdrive": (4.3667, 0.0),
        "aemeath_heavenfall_finale": (5.6667, 0.0),
        seraphic_id: (3.0, 1.3167),
        "aemeath_seraphic_duet_encore": (2.4167, 1.3333),
    }
    for action_id, (action_time, combat_time_cost) in expected.items():
        action = actions[action_id]
        assert_time(action, action_time, combat_time_cost)
        assert_has_damage_payload(action)
    return seraphic_id


def test_fallback_behavior() -> None:
    actions = actions_by_id()
    fallback_action = next(
        action
        for action in actions.values()
        if action.get("action_time") is not None and "combat_time_cost" not in action and action.get("hits")
    )
    model = ActionData.model_validate(fallback_action)
    assert approx(model.effective_combat_time_cost, model.effective_action_time), (
        "Actions without combat_time_cost should fall back to action_time"
    )


def test_combat_clock_execution() -> None:
    sim = Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])
    sim.state.resonance_energy["aemeath"] = 125.0
    assert sim.execute_action("aemeath_resonance_liberation")
    entry = sim.timeline[-1]

    assert entry.resolved_action_id == "aemeath_liberation_overdrive"
    assert approx(sim.state.current_time, 4.3667)
    assert approx(sim.state.combat_time, 0.0)
    assert approx(entry.action_time, 4.3667)
    assert approx(entry.combat_time_cost, 0.0)
    assert approx(entry.time_end - entry.time_start, 4.3667)
    assert approx(entry.combat_time_end - entry.combat_time_start, 0.0)

    assert sim.execute_action("short_wait")
    assert approx(sim.state.current_time, 4.8667)
    assert approx(sim.state.combat_time, 0.5)


def main() -> None:
    seraphic_id = test_whitelist_action_data()
    test_fallback_behavior()
    test_combat_clock_execution()
    print(f"Aemeath time-stop timing smoke test passed using {seraphic_id}.")


if __name__ == "__main__":
    main()
