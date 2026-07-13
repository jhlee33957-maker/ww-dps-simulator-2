from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import (  # noqa: E402
    COMBAT_STATE_FIELD_CLASSIFICATION,
    assert_combat_state_classification_complete,
    clone_simulation_for_search,
    future_state_fingerprint,
)
from simulator.models import CombatState  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    assert_combat_state_classification_complete()
    assert set(COMBAT_STATE_FIELD_CLASSIFICATION) == set(CombatState.model_fields)
    sim = _sim()
    same = clone_simulation_for_search(sim)
    assert future_state_fingerprint(sim) == future_state_fingerprint(same)
    same.state.total_damage += 999.0
    assert future_state_fingerprint(sim) == future_state_fingerprint(same)
    changed = clone_simulation_for_search(sim)
    changed.state.cooldowns["aemeath_basic_attack"] = 1.0
    assert future_state_fingerprint(sim) != future_state_fingerprint(changed)
    diagnostic = clone_simulation_for_search(sim)
    diagnostic.state.action_log.append({"debug": "ignored"})
    diagnostic.state.damage_log.append({"debug": "ignored"})
    assert future_state_fingerprint(sim) == future_state_fingerprint(diagnostic)
    assert "observation" not in future_state_fingerprint.__name__
    print("beam_search_state_fingerprint_contract_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(ROOT / "data", selected_character_ids="aemeath_mornye_lynae_enabled_test_party", initial_active_character="aemeath")


if __name__ == "__main__":
    main()

