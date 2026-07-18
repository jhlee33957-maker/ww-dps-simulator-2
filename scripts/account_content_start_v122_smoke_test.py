from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.account_config_contract import load_account_content_start, validate_content_start
from simulator.account_constellation_effects import apply_precombat_constellation_state


def rejected(payload: dict) -> None:
    try:
        validate_content_start(payload)
    except ValueError:
        return
    raise AssertionError("invalid account content-start contract unexpectedly passed")


def initial_state(precombat: float, optical: bool) -> dict:
    state = {"aemeath": {"sequence": 6}, "lynae": {"sequence": 2}}
    return apply_precombat_constellation_state(state, precombat, optical_sampling_active=optical)


def main() -> None:
    content = load_account_content_start(ROOT)
    validate_content_start(content)
    assert content["precombat_elapsed_seconds"] == 4.01 > 4.0
    assert content["account_optical_sampling_active"] is True
    state = initial_state(4.01, True)
    assert state["aemeath"]["radiance_quick_charge_ready"] is True
    assert state["lynae"]["overflow_restored_precombat"] == 120.0
    assert initial_state(4.0, True)["aemeath"]["radiance_quick_charge_ready"] is False
    assert initial_state(2.0, True)["lynae"]["overflow_restored_precombat"] == 0.0
    assert initial_state(4.01, False)["lynae"]["overflow_restored_precombat"] == 0.0
    for key, value in (
        ("precombat_elapsed_seconds", 4.0),
        ("aemeath_resonance_mode", "fusion_burst"),
        ("initial_active_character", "aemeath"),
        ("scope_id", "multi_target"),
    ):
        mutation = copy.deepcopy(content)
        mutation[key] = value
        rejected(mutation)
    print("account_content_start_v122_smoke_test ok")


if __name__ == "__main__":
    main()
