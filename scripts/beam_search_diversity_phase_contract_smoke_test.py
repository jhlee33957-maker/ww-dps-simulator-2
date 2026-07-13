from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_state import clone_simulation_for_search, diversity_key, diversity_quantization_contract  # noqa: E402
from simulator.models import ActiveBuff, ScheduledEffectState  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    base = _sim()
    base_key = diversity_key(base)
    contract = diversity_quantization_contract()
    assert contract["scheduled_effect_phase_band_seconds"] == 0.5
    assert contract["scheduled_effect_remaining_band_seconds"] == 1.0
    assert contract["active_buff_remaining_band_seconds"] == 1.0
    assert contract["declared_mechanic_field_encoders"]["mornye"]["syntony_field_remaining"] == {
        "encoder": "active_remaining_band",
        "band": 5.0,
    }
    scheduled = clone_simulation_for_search(base)
    scheduled.state.scheduled_effects.append(
        ScheduledEffectState(
            instance_id="phase-a",
            effect_id="phase-effect",
            source_character_id="mornye",
            payload_action_id="mornye_syntony_field_damage",
            remaining_duration=11.0,
            tick_interval=3.0,
            time_until_next_tick=0.2,
            trigger_count=1,
            max_trigger_count=4,
            payload_event_type="damage",
            scheduled_resource_policy="source_confirmed_positive_gains",
            source_status="test",
        )
    )
    phase_key = diversity_key(scheduled)
    assert phase_key != base_key
    for phase in (0.9, 1.4, 2.9):
        shifted = clone_simulation_for_search(scheduled)
        shifted.state.scheduled_effects[0].time_until_next_tick = phase
        assert 0.0 <= shifted.state.scheduled_effects[0].time_until_next_tick <= shifted.state.scheduled_effects[0].tick_interval
        assert diversity_key(shifted) != phase_key
    status = clone_simulation_for_search(base)
    status.state.scheduled_effects.append(
        ScheduledEffectState(
            instance_id="status-a",
            effect_id="spray-paint",
            source_character_id="lynae",
            payload_action_id="lynae_spray_paint_application",
            remaining_duration=5.0,
            tick_interval=5.0,
            time_until_next_tick=5.0,
            payload_event_type="status_application",
            scheduled_resource_policy="none",
            source_status="test",
        )
    )
    assert diversity_key(status) != base_key
    buffed = clone_simulation_for_search(base)
    buffed.state.active_buffs.append(ActiveBuff(buff_id="buff-a", source_character_id="aemeath", target_character_id="mornye", remaining_duration=1.0, stack_count=1))
    buff_key = diversity_key(buffed)
    buff_phase = clone_simulation_for_search(buffed)
    buff_phase.state.active_buffs[0].remaining_duration = 4.9
    assert diversity_key(buff_phase) != buff_key
    buffed.state.active_buffs[0].target_character_id = "lynae"
    assert diversity_key(buffed) != buff_key
    buffed.state.active_buffs[0].target_character_id = "mornye"
    buffed.state.active_buffs[0].stack_count = 2
    assert diversity_key(buffed) != buff_key
    print("beam_search_diversity_phase_contract_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


if __name__ == "__main__":
    main()
