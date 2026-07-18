from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
    account = sim.state.character_mechanics_state["_account_constellation"]
    account.update({"aemeath_s3_tune_contributors": ["aemeath", "lynae", "mornye"], "aemeath_s3_tune_crit_damage_bonus": 0.6, "aemeath_s3_tune_finale_deepen": 0.25})
    state = sim.state.character_mechanics_state["aemeath"]
    state.update({"heavenfall_unbound": True, "heavenfall_unbound_remaining": 30.0, "synchronization_rate": 200.0, "resonance_rate": 4.0})
    assert sim.execute_action("aemeath_heavenfall_finale")
    hit = sim.last_action_result.hit_details[0]
    assert round(hit["account_crit_damage_after"] - hit["account_crit_damage_before"], 4) == 0.6
    assert hit["account_damage_amp_add"] == 0.65
    print("aemeath_s3_crit_damage_runtime_v121_smoke_test ok")


if __name__ == "__main__":
    main()
