from __future__ import annotations

import sys
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import (  # noqa: E402
    COMPACT_STATE_FIELDS,
    COMBAT_STATE_FIELD_AUDIT,
    COMBAT_STATE_FIELD_CLASSIFICATION,
    OBJECTIVE_ONLY_FIELDS,
    assert_combat_state_classification_complete,
    future_state_fingerprint,
    serialize_simulation_state,
    state_payload_size_bytes,
)
from simulator.models import CombatState  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    assert_combat_state_classification_complete()
    assert set(COMBAT_STATE_FIELD_CLASSIFICATION) == set(CombatState.model_fields)
    assert set(COMBAT_STATE_FIELD_AUDIT) == set(CombatState.model_fields)
    assert "total_damage" in COMPACT_STATE_FIELDS
    for field_name in OBJECTIVE_ONLY_FIELDS - {"total_damage"}:
        assert field_name not in COMPACT_STATE_FIELDS, field_name
        audit = COMBAT_STATE_FIELD_AUDIT[field_name]
        assert audit["classification"] == "objective_only"
        for key in ("action_availability_input", "transition_selection_input", "damage_formula_input", "cooldown_resource_update_input", "scheduled_effect_behavior_input", "mechanic_hook_input"):
            assert audit[key] is False, (field_name, key)
    sim = _sim()
    before_fingerprint = future_state_fingerprint(sim)
    before_size = state_payload_size_bytes(sim)
    sim.state.wasted_resonance_energy["aemeath"] = 999.0
    sim.state.wasted_concerto_energy["aemeath"] = 888.0
    sim.state.off_tune_accumulated_total = 777.0
    sim.state.tune_response_events.append({"diagnostic": "objective-only"})
    for field_name in KNOWN_REPORTING_COUNTERS:
        setattr(sim.state, field_name, getattr(sim.state, field_name) + 7)
    sim.state.action_log.extend({"debug": index} for index in range(200))
    payload = serialize_simulation_state(sim)
    assert future_state_fingerprint(sim) == before_fingerprint
    assert state_payload_size_bytes(sim) == before_size
    for field_name in ("wasted_resonance_energy", "tune_response_events", "action_log", *KNOWN_REPORTING_COUNTERS):
        assert field_name not in payload["state"]
        assert field_name in payload["omitted_fields"]
    future = _sim()
    future_before = future_state_fingerprint(future)
    future.state.enemy_off_tune_current += 10.0
    assert future_state_fingerprint(future) != future_before
    result = subprocess.run([sys.executable, "scripts/beam_search_clone_behavioral_parity_smoke_test.py"], cwd=ROOT, text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    print("beam_search_future_field_classification_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


KNOWN_REPORTING_COUNTERS = (
    "enemy_mistune_entered_count",
    "off_tune_accumulation_blocked_by_tune_break_cooldown_count",
    "interfered_marker_applied_count",
    "interfered_marker_direct_damage_amp_applied_action_count",
    "aemeath_starburst_trigger_count",
    "mornye_particle_jet_trigger_count",
    "lynae_spectral_analysis_trigger_count",
    "aemeath_starburst_cooldown_blocked_count",
    "mornye_particle_jet_cooldown_blocked_count",
    "lynae_spectral_analysis_cooldown_blocked_count",
    "tune_break_action_used_count",
    "starfield_calibrator_concerto_restored_total",
)


if __name__ == "__main__":
    main()
