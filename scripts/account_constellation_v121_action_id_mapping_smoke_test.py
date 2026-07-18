from __future__ import annotations

from account_constellation_v121_runtime_test_utils import ROOT  # noqa: F401
from simulator.account_constellation_effects import (
    ACCOUNT_SCOPE_ID,
    aemeath_s1_charged_sync_gain,
    aemeath_s1_heavy_crit_damage,
    aemeath_s3_register_contributor,
    initialize_account_constellation_state,
)


def main() -> None:
    assert aemeath_s1_heavy_crit_damage(1.5, "aemeath_heavy_aemeath_charged_2", True) == 4.5
    assert aemeath_s1_heavy_crit_damage(1.5, "aemeath_heavy_mech_charged_2", True) == 4.5
    assert aemeath_s1_heavy_crit_damage(1.5, "aemeath_heavy_aemeath_charged_1", True) == 1.5
    assert aemeath_s1_heavy_crit_damage(1.5, "aemeath_heavy_mech_charged_1", True) == 1.5
    assert aemeath_s1_heavy_crit_damage(1.5, "aemeath_heavy_mech_charged_2_extra", True) == 1.5

    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_aemeath_charged_2") == 100.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_mech_charged_2") == 100.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_aemeath_charged_1") == 0.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_mech_charged_1") == 0.0
    assert aemeath_s1_charged_sync_gain(True, True, "aemeath_heavy_mech_charged_20") == 0.0

    state = initialize_account_constellation_state({"aemeath": {"sequence": 6}}, ACCOUNT_SCOPE_ID, 0.0)
    first = aemeath_s3_register_contributor(state, "fusion_burst", "aemeath")
    second = aemeath_s3_register_contributor(state, "fusion_burst", "mornye")
    assert first["finale_deepen"] == 0.0
    assert second["finale_deepen"] == 0.25
    print("account_constellation_v121_action_id_mapping_smoke_test ok")


if __name__ == "__main__":
    main()
