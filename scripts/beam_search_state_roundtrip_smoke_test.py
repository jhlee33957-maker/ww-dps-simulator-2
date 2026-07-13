from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import (  # noqa: E402
    assert_search_state_invariants,
    future_state_fingerprint,
    future_state_payload,
    restore_simulation_from_state,
    serialize_simulation_state,
)
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    sim = Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")
    assert sim.execute_action("aemeath_basic_attack")
    payload = serialize_simulation_state(sim)
    restored = restore_simulation_from_state(sim, payload)
    assert restored is not sim
    assert restored.state.character_states is restored.state.character_mechanics_state
    assert_search_state_invariants(restored.state)
    assert future_state_payload(restored) == future_state_payload(sim)
    assert future_state_fingerprint(restored) == future_state_fingerprint(sim)
    assert restored.timeline == []
    assert "timeline" in payload["omitted_fields"]
    assert "action_log" in payload["omitted_fields"]
    assert "character_states" in payload["omitted_fields"]
    assert restored.execute_action("aemeath_basic_attack")
    assert sim.state.combat_time < restored.state.combat_time
    print("beam_search_state_roundtrip_smoke_test ok")


if __name__ == "__main__":
    main()
