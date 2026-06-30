from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env.action_mask import action_mask
from simulator.simulation import Simulation


DATA_DIR = PROJECT_ROOT / "data"


def make_sim() -> Simulation:
    return Simulation.from_json(DATA_DIR, selected_character_ids=["aemeath"])


def state(sim: Simulation) -> dict:
    return sim.state.character_mechanics_state["aemeath"]


def derive(sim: Simulation) -> None:
    sim.character_mechanics["aemeath"].advance_time(sim.state, 0.0)


def set_energy(sim: Simulation) -> None:
    sim.state.resonance_energy["aemeath"] = 125.0


def make_unbound_state(sim: Simulation, sync: float, resonance_rate: float) -> dict:
    data = state(sim)
    data["heavenfall_unbound"] = True
    data["heavenfall_unbound_remaining"] = 60.0
    data["synchronization_rate"] = sync
    data["resonance_rate"] = resonance_rate
    derive(sim)
    return data


def assert_liberation_available(sim: Simulation, expected: bool) -> None:
    available = sim.is_action_available(sim.actions["aemeath_resonance_liberation"])
    assert available is expected, f"expected policy liberation availability {expected}, got {available}"
    in_mask = "aemeath_resonance_liberation" in sim.valid_action_ids()
    assert in_mask is expected, f"expected action mask availability {expected}, got {in_mask}"
    action_index = list(sim.policy_actions).index("aemeath_resonance_liberation")
    masked = bool(action_mask(sim)[action_index])
    assert masked is expected, f"expected env action mask availability {expected}, got {masked}"


def test_initial_state() -> None:
    sim = make_sim()
    set_energy(sim)
    data = state(sim)
    assert data["heavenfall_unbound"] is False
    assert data["synchronization_rate"] == 0.0
    assert data["resonance_rate"] == 0.0
    assert data["finale_available"] is False
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"
    assert_liberation_available(sim, True)


def test_overdrive_from_initial_state() -> None:
    sim = make_sim()
    set_energy(sim)
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_liberation_overdrive"
    assert sim.execute_action("aemeath_resonance_liberation")
    data = state(sim)
    assert data["form"] == "mech"
    assert data["heavenfall_unbound"] is True
    assert data["heavenfall_unbound_remaining"] == 60.0
    assert data["synchronization_rate"] == 30.0
    assert data["resonance_rate"] == 1.0
    assert data["stardust_resonance_remaining"] > 0.0
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["finale_available"] is False


def test_overdrive_does_not_immediately_allow_finale() -> None:
    sim = make_sim()
    set_energy(sim)
    assert sim.execute_action("aemeath_resonance_liberation")
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert sim.resolve_action_id("aemeath_resonance_skill") != "aemeath_heavenfall_finale"
    assert_liberation_available(sim, False)
    assert not sim.execute_action("aemeath_resonance_liberation")
    resolved_ids = [row.resolved_action_id for row in sim.timeline]
    assert resolved_ids == ["aemeath_liberation_overdrive"]


def test_instant_response_without_finale() -> None:
    sim = make_sim()
    make_unbound_state(sim, sync=199.0, resonance_rate=4.0)
    assert state(sim)["instant_response"] is True
    assert state(sim)["finale_available"] is False
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert_liberation_available(sim, False)


def test_sync_cap_without_resonance_cap() -> None:
    sim = make_sim()
    make_unbound_state(sim, sync=200.0, resonance_rate=3.0)
    assert state(sim)["instant_response"] is False
    assert state(sim)["finale_available"] is False
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert_liberation_available(sim, False)


def test_finale_ready() -> None:
    sim = make_sim()
    make_unbound_state(sim, sync=200.0, resonance_rate=4.0)
    assert state(sim)["instant_response"] is True
    assert state(sim)["finale_available"] is True
    assert sim.resolve_action_id("aemeath_resonance_liberation") == "aemeath_heavenfall_finale"
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"
    assert_liberation_available(sim, True)


def test_finale_effect() -> None:
    sim = make_sim()
    make_unbound_state(sim, sync=200.0, resonance_rate=4.0)
    state(sim)["stardust_resonance_remaining"] = 30.0
    state(sim)["seraphic_duo_remaining"] = 5.0
    assert sim.execute_action("aemeath_resonance_liberation")
    data = state(sim)
    assert data["form"] == "aemeath"
    assert data["synchronization_rate"] == 0.0
    assert data["resonance_rate"] == 0.0
    assert data["heavenfall_unbound"] is False
    assert data["heavenfall_unbound_remaining"] == 0.0
    assert data["stardust_resonance_remaining"] == 0.0
    assert data["seraphic_duo_remaining"] == 0.0
    assert data["instant_response"] is False
    assert data["finale_available"] is False
    assert sim.timeline[-1].resolved_action_id == "aemeath_heavenfall_finale"


def test_cooldown_separation() -> None:
    sim = make_sim()
    overdrive = sim.actions["aemeath_liberation_overdrive"]
    finale = sim.actions["aemeath_heavenfall_finale"]
    assert overdrive.cooldown_group == "aemeath_overdrive"
    assert finale.cooldown_group == "aemeath_finale"
    make_unbound_state(sim, sync=200.0, resonance_rate=4.0)
    sim.state.cooldowns["aemeath_overdrive"] = 25.0
    assert sim.is_action_available(sim.actions["aemeath_resonance_liberation"])
    assert sim.execute_action("aemeath_resonance_liberation")
    assert "aemeath_finale" in sim.state.cooldowns


def test_seraphic_duet_vs_finale_priority() -> None:
    sim = make_sim()
    make_unbound_state(sim, sync=200.0, resonance_rate=4.0)
    data = state(sim)
    data["form"] = "aemeath"
    data["seraphic_duo_remaining"] = 5.0
    derive(sim)
    assert sim.resolve_action_id("aemeath_resonance_skill") == "aemeath_heavenfall_finale"
    assert sim.resolve_action_id("aemeath_resonance_skill") != "aemeath_seraphic_duet_overturn"


def test_two_liberation_regression() -> None:
    sim = make_sim()
    set_energy(sim)
    assert sim.execute_action("aemeath_resonance_liberation")
    assert not sim.execute_action("aemeath_resonance_liberation")
    resolved_ids = [row.resolved_action_id for row in sim.timeline]
    assert resolved_ids == ["aemeath_liberation_overdrive"]
    assert ["aemeath_liberation_overdrive", "aemeath_heavenfall_finale"] != resolved_ids[:2]


def main() -> None:
    test_initial_state()
    test_overdrive_from_initial_state()
    test_overdrive_does_not_immediately_allow_finale()
    test_instant_response_without_finale()
    test_sync_cap_without_resonance_cap()
    test_finale_ready()
    test_finale_effect()
    test_cooldown_separation()
    test_seraphic_duet_vs_finale_priority()
    test_two_liberation_regression()
    print("Aemeath finale condition smoke test passed.")


if __name__ == "__main__":
    main()
