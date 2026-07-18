from __future__ import annotations

from account_constellation_v121_runtime_test_utils import ACCOUNT_BUILD_OVERRIDES, make_account_sim, ready_lynae_visual_impact
from env.observation_features import build_observation_values as build_v5_observation_values
from env.wuwa_env import WuwaDpsEnv
from simulator.account_constellation_effects import ACCOUNT_OBSERVATION_SHAPE, ACCOUNT_OBSERVATION_VERSION, ACCOUNT_SCOPE_ID


def main() -> None:
    sim = make_account_sim("lynae")
    v5 = build_v5_observation_values(sim)
    v6 = sim.account_observation_values()
    assert len(v5) == 314
    assert len(v6) == ACCOUNT_OBSERVATION_SHAPE == 330
    assert v6[:314] == v5
    assert any(value != 0.0 for value in v6[:314])
    assert sim.account_observation_metadata()["observation_version"] == ACCOUNT_OBSERVATION_VERSION

    ready_lynae_visual_impact(sim)
    assert sim.execute_action("lynae_visual_impact")
    with_paint = sim.account_observation_values()
    assert with_paint[325] == 1.0
    assert sim.execute_action("short_wait")
    after_wait = sim.account_observation_values()
    assert 0.0 < after_wait[325] < with_paint[325]

    env = WuwaDpsEnv(
        "data",
        selected_character_ids=["aemeath", "lynae", "mornye"],
        initial_active_character="aemeath",
        build_profile_overrides=ACCOUNT_BUILD_OVERRIDES,
        account_simulation_scope=ACCOUNT_SCOPE_ID,
        precombat_elapsed_seconds=5.0,
        account_optical_sampling_active=True,
    )
    assert env.observation_space.shape == (330,)
    assert env.observation_version == ACCOUNT_OBSERVATION_VERSION
    assert len(env._get_observation()) == 330
    print("account_constellation_v121_real_observation_smoke_test ok")


if __name__ == "__main__":
    main()
