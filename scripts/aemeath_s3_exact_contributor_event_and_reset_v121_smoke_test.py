from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def main() -> None:
    sim = make_account_sim("aemeath")
    account = sim.state.character_mechanics_state["_account_constellation"]
    assert sim.execute_action("aemeath_echo_sigillum")
    assert account["aemeath_s3_fusion_contributors"] == []
    sim.state.mechanics_config.setdefault("aemeath", {})["aemeath_resonance_mode"] = "fusion_burst"
    sim.state.character_mechanics_state["aemeath"]["instant_response"] = True
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    assert account["aemeath_s3_fusion_contributors"] == ["aemeath"]
    sim.state.mechanics_config["aemeath"]["aemeath_resonance_mode"] = "tune_rupture"
    sim.state.character_mechanics_state["aemeath"]["instant_response"] = True
    assert sim.execute_action("aemeath_heavy_aemeath_charged_2")
    assert account["aemeath_s3_fusion_contributors"] == []
    print("aemeath_s3_exact_contributor_event_and_reset_v121_smoke_test ok")


if __name__ == "__main__":
    main()
