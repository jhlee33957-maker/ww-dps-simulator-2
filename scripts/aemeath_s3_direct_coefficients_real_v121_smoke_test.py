from __future__ import annotations

from account_constellation_v121_runtime_test_utils import make_account_sim


def _hit(sim, action_id: str):
    assert sim.execute_action(action_id)
    return next(hit for hit in sim.last_action_result.hit_details if not hit.get("is_generated_mechanic_damage"))


def main() -> None:
    sim = make_account_sim("aemeath")
    state = sim.state.character_mechanics_state["aemeath"]
    state.update({"heavenfall_unbound": True, "heavenfall_unbound_remaining": 30.0, "synchronization_rate": 200.0, "resonance_rate": 4.0})
    finale = _hit(sim, "aemeath_heavenfall_finale")
    assert finale["effective_coefficient"] == finale["base_coefficient"] * 2.0
    sim = make_account_sim("aemeath")
    overdrive = _hit(sim, "aemeath_liberation_overdrive")
    assert overdrive["effective_coefficient"] == overdrive["base_coefficient"] * 1.4
    print("aemeath_s3_direct_coefficients_real_v121_smoke_test ok")


if __name__ == "__main__":
    main()
