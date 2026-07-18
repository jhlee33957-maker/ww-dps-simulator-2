from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def _ready_tune_break(sim, active_character_id: str) -> None:
    sim.state.active_character_id = active_character_id
    sim.state.enemy_tune_break_available = True
    sim.state.enemy_tune_break_cooldown_remaining = 0.0
    sim.state.target_tune_shift_state = "tune_rupture_shifting"
    sim.state.target_interfered_state = "tune_rupture_interfered"


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    for character_id, action_id in (
        ("aemeath", "aemeath_tune_break"),
        ("lynae", "lynae_tune_break"),
        ("mornye", "mornye_tune_break"),
    ):
        _ready_tune_break(sim, character_id)
        assert sim.execute_action(action_id)

    account = sim.state.character_mechanics_state["_account_constellation"]
    assert account["aemeath_s3_tune_contributors"] == ["aemeath", "lynae", "mornye"]
    assert account["aemeath_s3_tune_crit_damage_bonus"] == 0.6000000000000001
    assert account["aemeath_s3_tune_finale_deepen"] == 0.25

    aemeath_state = sim.state.character_mechanics_state["aemeath"]
    aemeath_state["heavenfall_unbound"] = True
    aemeath_state["heavenfall_unbound_remaining"] = 30.0
    aemeath_state["synchronization_rate"] = 200.0
    aemeath_state["resonance_rate"] = 4.0
    sim.state.active_character_id = "aemeath"
    assert sim.execute_action("aemeath_heavenfall_finale")
    hit = sim.last_action_result.hit_details[0]
    assert hit["account_damage_amp_add"] == 0.65
    assert round(hit["account_crit_damage_after"] - hit["account_crit_damage_before"], 4) == 0.6
    assert any(
        event["event_type"] == "aemeath_s3_finale_deepen_formula"
        for event in hit["account_constellation_damage_context"]
    )
    print("aemeath_s3_real_contributor_runtime_v121_smoke_test ok")


if __name__ == "__main__":
    main()
