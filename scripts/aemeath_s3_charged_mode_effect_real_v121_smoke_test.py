from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    for action_id in ("aemeath_heavy_aemeath_charged_2", "aemeath_heavy_mech_charged_2"):
        sim = make_account_sim("aemeath")
        sim.state.character_mechanics_state["aemeath"].update({"instant_response": True, "form": "mech" if "mech" in action_id else "aemeath"})
        sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "tune_rupture"
        assert sim.execute_action(action_id)
        assert "tune_rupture_shifting" in sim.last_action_result.emitted_mechanic_event_tags
        assert sim.state.target_tune_shift_state == "tune_rupture_shifting"
    print("aemeath_s3_charged_mode_effect_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
