from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.echo_sets import pact_neonlight_incoming_atk_percent
from simulator.simulation import Simulation


def main() -> None:
    assert pact_neonlight_incoming_atk_percent(0)["total"] == 0.15
    assert abs(pact_neonlight_incoming_atk_percent(40)["total"] - 0.27) < 1e-9
    assert pact_neonlight_incoming_atk_percent(50)["total"] == 0.30
    assert pact_neonlight_incoming_atk_percent(100)["total"] == 0.30

    sim = Simulation.from_json(ROOT / "data", party="aemeath_lynae_enabled_test_party")
    sim.state.concerto_energy["lynae"] = 100.0
    assert sim.execute_action("swap_to_aemeath")
    row = sim.state.action_log[-1]
    assert row["pact_neonlight_incoming_atk_buff"] is True
    assert row["pact_neonlight_incoming_atk_base"] == 0.15
    assert row["pact_neonlight_source_status"] == "user_supplied_echo_set_tooltip"
    lynae = sim.characters["lynae"]
    assert lynae.echo_sets["pact_of_neonlight_leap"]["static_2set_spectro_already_in_profile"] is True
    assert "pact_neonlight_incoming_atk" in row["applied_buffs"]
    print("pact_neonlight_leap_5set_smoke_test ok")


if __name__ == "__main__":
    main()
