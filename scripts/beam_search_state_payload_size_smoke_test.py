from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import serialize_simulation_state, sequence_sha256, state_payload_size_bytes  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


PAYLOAD_LIMIT = 65536


def main() -> None:
    route = json.loads((ROOT / "data" / "manual_120s_baseline_routes_v104.json").read_text(encoding="utf-8-sig"))
    selected = route["routes"]["primary"]["selected_policy_actions"]
    sim = _sim()
    size_at_30 = None
    for action_id in selected:
        assert sim.execute_action(action_id), action_id
        if size_at_30 is None and sim.state.combat_time >= 30.0:
            size_at_30 = state_payload_size_bytes(sim)
            assert size_at_30 < PAYLOAD_LIMIT, size_at_30
    size_at_120 = state_payload_size_bytes(sim)
    assert size_at_30 is not None
    assert size_at_120 < PAYLOAD_LIMIT, size_at_120
    full_state_bytes = len(json.dumps(sim.state.model_dump(mode="json"), ensure_ascii=False).encode("utf-8"))
    compact_bytes = len(json.dumps(serialize_simulation_state(sim), ensure_ascii=False).encode("utf-8"))
    assert compact_bytes < full_state_bytes / 20, (compact_bytes, full_state_bytes)
    before = state_payload_size_bytes(sim)
    sim.state.action_log.extend({"debug": index} for index in range(1000))
    sim.state.damage_log.extend({"debug": index} for index in range(1000))
    after = state_payload_size_bytes(sim)
    assert before == after
    resolved = [entry.resolved_action_id for entry in sim.timeline]
    assert sequence_sha256(selected) == "e3ddea873cb5059bd29a8a9eb7165ea0e45a9a9e4fa4f68e5e229db2f622daf1"
    assert sequence_sha256(resolved) == "3edca6f6f258999a9c915a9ec32ee88c0db570d2303846e0fb8b6da367970229"
    print(f"beam_search_state_payload_size_smoke_test ok size_30={size_at_30} size_120={size_at_120}")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


if __name__ == "__main__":
    main()
