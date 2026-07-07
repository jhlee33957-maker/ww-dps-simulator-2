from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.simulation import Simulation


def liberation_damage(with_buffs: bool) -> float:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.resonance_energy["aemeath"] = sim.characters["aemeath"].resonance_energy_max
    if with_buffs:
        assert sim.execute_action("lynae_resonance_liberation")
        sim.state.concerto_energy["lynae"] = 100.0
        assert sim.execute_action("swap_to_aemeath")
    else:
        sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_resonance_liberation")
    return sim.state.action_log[-1]["damage"]


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    assert sim.execute_action("lynae_resonance_liberation")
    row = sim.state.action_log[-1]
    assert "lynae_liberation_party_damage_amp" in row["applied_buffs"]
    assert row["lynae_liberation_party_damage_buff_active"] is True
    assert row["lynae_liberation_party_damage_buff_value"] == 0.24

    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.state.action_log[-1]
    assert row["lynae_outro_all_damage_amp_value"] == 0.15
    assert row["lynae_outro_liberation_damage_amp_value"] == 0.25
    assert "lynae_outro_all_damage_amp" in row["applied_buffs"]
    assert "lynae_outro_liberation_damage_amp" in row["applied_buffs"]

    assert liberation_damage(True) > liberation_damage(False)
    print("lynae_liberation_outro_buff_smoke_test ok")


if __name__ == "__main__":
    main()
