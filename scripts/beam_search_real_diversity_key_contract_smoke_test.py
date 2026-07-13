from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search.beam_reporting import select_damage_only_winner  # noqa: E402
from search.beam_state import clone_simulation_for_search, diversity_key, diversity_quantization_contract  # noqa: E402
from simulator.models import ActiveBuff, ScheduledEffectState  # noqa: E402
from simulator.simulation import Simulation  # noqa: E402


def main() -> None:
    base = _sim()
    base_key = diversity_key(base)
    contract = diversity_quantization_contract()
    assert contract["route_blind"] is True
    assert contract["combo_and_forced_stage_encoding"] == "exact_categorical"
    assert contract["scheduled_effect_phase_band_seconds"] == 0.5
    assert contract["scheduled_effect_remaining_band_seconds"] == 1.0
    assert contract["active_buff_remaining_band_seconds"] == 1.0
    assert contract["declared_mechanic_field_encoders"]["aemeath"]["sync_strike_window_remaining"] == {
        "encoder": "active_remaining_band",
        "band": 0.5,
    }
    assert contract["declared_mechanic_field_encoders"]["lynae"]["visual_impact_cooldown_remaining"] == {
        "encoder": "cooldown_ready_remaining_band",
        "band": 1.0,
    }
    mutations = [
        lambda sim: setattr(sim.state, "active_character_id", "mornye"),
        lambda sim: sim.state.resonance_energy.__setitem__("aemeath", 25.0),
        lambda sim: sim.state.concerto_energy.__setitem__("aemeath", 25.0),
        lambda sim: setattr(sim.state, "enemy_off_tune_current", sim.state.enemy_off_tune_max * 0.25),
        lambda sim: setattr(sim.state, "rupturous_trail_stacks", 10),
        lambda sim: sim.state.cooldowns.__setitem__("aemeath_resonance_skill", 1.0),
        lambda sim: sim.state.active_buffs.append(ActiveBuff(buff_id="test_buff", source_character_id="aemeath", remaining_duration=5.0)),
        lambda sim: sim.state.scheduled_effects.append(
            ScheduledEffectState(
                instance_id="test-instance",
                effect_id="test-effect",
                source_character_id="aemeath",
                payload_action_id="short_wait",
                remaining_duration=5.0,
                tick_interval=1.0,
                time_until_next_tick=1.0,
                source_status="test",
            )
        ),
        lambda sim: sim.state.character_mechanics_state["aemeath"].__setitem__("form", "mech"),
        lambda sim: sim.state.character_mechanics_state["aemeath"].__setitem__("aemeath_combo_stage", 2),
        lambda sim: sim.state.character_mechanics_state["aemeath"].__setitem__("synchronization_rate", 25.0),
        lambda sim: sim.state.character_mechanics_state["mornye"].__setitem__("baseline_combo_stage", 2),
        lambda sim: sim.state.character_mechanics_state["mornye"].__setitem__("rest_mass_energy", 25.0),
        lambda sim: sim.state.character_mechanics_state["mornye"].__setitem__("mode", "wide_field_observation"),
        lambda sim: sim.state.character_mechanics_state["lynae"].__setitem__("overflow", 25.0),
        lambda sim: sim.state.character_mechanics_state["lynae"].__setitem__("true_color", 5.0),
        lambda sim: sim.state.character_mechanics_state["lynae"].__setitem__("basic_combo_stage", 2),
        lambda sim: sim.state.character_mechanics_state["lynae"].__setitem__("next_basic_forced_stage", "stage_4"),
        lambda sim: sim.state.character_mechanics_state["lynae"].__setitem__("lynae_resonance_mode", "tune_strain"),
    ]
    for mutate in mutations:
        changed = clone_simulation_for_search(base)
        mutate(changed)
        assert diversity_key(changed) != base_key
    scheduled = clone_simulation_for_search(base)
    scheduled.state.scheduled_effects.append(
        ScheduledEffectState(
            instance_id="phase-band",
            effect_id="phase-band",
            source_character_id="aemeath",
            payload_action_id="short_wait",
            remaining_duration=5.1,
            tick_interval=3.0,
            time_until_next_tick=0.4,
            source_status="test",
        )
    )
    scheduled_key = diversity_key(scheduled)
    scheduled.state.scheduled_effects[0].time_until_next_tick = 0.6
    assert diversity_key(scheduled) != scheduled_key
    scheduled.state.scheduled_effects[0].time_until_next_tick = 0.4
    scheduled.state.scheduled_effects[0].remaining_duration = 4.9
    assert diversity_key(scheduled) != scheduled_key
    buffed = clone_simulation_for_search(base)
    buffed.state.active_buffs.append(ActiveBuff(buff_id="band_buff", source_character_id="aemeath", target_character_id="mornye", remaining_duration=1.0))
    buffed_key = diversity_key(buffed)
    buffed.state.active_buffs[0].remaining_duration = 2.0
    assert diversity_key(buffed) != buffed_key
    forbidden = diversity_key(base).lower()
    for token in ("manual", "route", "ppo", "bc_model", "probability"):
        assert token not in forbidden
    winner = select_damage_only_winner([{"winner_kind": "beam_search_route", "total_damage": 5165134.682363356, "declared_order": 1}])
    assert winner["winner_kind"] == "verified_bc_model"
    higher = select_damage_only_winner([{"winner_kind": "beam_search_route", "total_damage": 5165134.682365, "declared_order": 1}])
    assert higher["winner_kind"] == "beam_search_route"
    print("beam_search_real_diversity_key_contract_smoke_test ok")


def _sim() -> Simulation:
    return Simulation.from_json(
        ROOT / "data",
        selected_character_ids="aemeath_mornye_lynae_enabled_test_party",
        initial_active_character="aemeath",
    )


if __name__ == "__main__":
    main()
