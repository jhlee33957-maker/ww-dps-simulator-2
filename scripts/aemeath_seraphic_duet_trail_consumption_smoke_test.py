from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def ready_sim(*, preserve: bool) -> Simulation:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    data = sim.state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    data["trail_no_cost_remaining"] = 30.0 if preserve else 0.0
    sim.state.rupturous_trail_stacks = 20
    sim.state.rupturous_trail_remaining = 30.0
    return sim


def main() -> None:
    preserved = ready_sim(preserve=True)
    assert preserved.execute_action("aemeath_seraphic_duet_overturn")
    first = preserved.timeline[-1]
    assert first.aemeath_seraphic_duet_trail_preservation_active is True
    assert first.aemeath_seraphic_duet_trail_consumed is False
    assert preserved.state.rupturous_trail_stacks == 20

    data = preserved.state.character_mechanics_state["aemeath"]
    data["form"] = "aemeath"
    data["synchronization_rate"] = 100.0
    data["seraphic_duo_remaining"] = 5.0
    preserved.state.cooldowns.clear()
    assert preserved.execute_action("aemeath_seraphic_duet_overturn")
    second = preserved.timeline[-1]
    assert second.aemeath_seraphic_duet_trail_preservation_active is False
    assert second.aemeath_seraphic_duet_trail_consumed is True
    assert preserved.state.rupturous_trail_stacks == 0

    consumed = ready_sim(preserve=False)
    assert consumed.execute_action("aemeath_seraphic_duet_overturn")
    assert consumed.timeline[-1].aemeath_rupturous_trail_stacks_consumed == 20
    assert consumed.state.rupturous_trail_stacks == 0
    print("aemeath_seraphic_duet_trail_consumption_smoke_test ok")


if __name__ == "__main__":
    main()
