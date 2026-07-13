from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.full_real_cycle_integration import assert_close
from scripts.manual_120s_baseline import execute_route


EXPECTED_RESONANCE = {
    "initial": {"aemeath": 125.0, "mornye": 175.0, "lynae": 125.0},
    "gained": {"aemeath": 173.72000000000003, "mornye": 360.5763839999999, "lynae": 247.90212000000002},
    "spent": {"aemeath": 250.00000000000003, "mornye": 525.0, "lynae": 250.0},
    "wasted": {"aemeath": 27.400000000000077, "mornye": 56.68230399999996, "lynae": 77.49212000000001},
    "final": {"aemeath": 48.71999999999999, "mornye": 10.576384000000001, "lynae": 122.90212000000002},
}

EXPECTED_CONCERTO = {
    "initial": {"aemeath": 0.0, "mornye": 0.0, "lynae": 0.0},
    "gained": {"aemeath": 300.00000000000006, "mornye": 336.0, "lynae": 388.5899999999999},
    "spent": {"aemeath": 300.00000000000006, "mornye": 336.0, "lynae": 299.99999999999994},
    "wasted": {"aemeath": 10.019999999999982, "mornye": 50.05000000000001, "lynae": 2.0},
    "final": {"aemeath": 0.0, "mornye": 0.0, "lynae": 88.58999999999999},
}


def _assert_resource(actual: dict, expected: dict, label: str) -> None:
    for bucket, values in expected.items():
        for character, expected_value in values.items():
            assert_close(actual[bucket][character], expected_value, f"{label} {bucket} {character}", 1e-9)
    for character in expected["initial"]:
        assert_close(
            actual["initial"][character] + actual["gained"][character] - actual["spent"][character],
            actual["final"][character],
            f"{label} conservation {character}",
            1e-9,
        )


def main() -> None:
    result = execute_route("primary")
    _assert_resource(result["resonance_energy"], EXPECTED_RESONANCE, "resonance")
    _assert_resource(result["concerto_energy"], EXPECTED_CONCERTO, "concerto")

    sigillum_re_events = [
        event
        for event in result["resonance_energy"]["scheduled"]["events"]
        if event["source_action_id"] == "aemeath_echo_sigillum"
    ]
    assert sigillum_re_events
    assert {event["recipient"] for event in sigillum_re_events} == {"aemeath"}

    mornye_scheduled = [
        event
        for event in result["resonance_energy"]["scheduled"]["events"] + result["concerto_energy"]["scheduled"]["events"]
        if event["source_character_id"] == "mornye"
    ]
    assert mornye_scheduled
    assert {event["recipient"] for event in mornye_scheduled} == {"mornye"}

    transitions = [
        event for event in result["resonance_energy"]["direct"]["events"] + result["concerto_energy"]["direct"]["events"]
        if str(event["resolved_action_id"]).startswith("transition:")
    ]
    assert transitions
    assert all(event["recipient"] in {"aemeath", "mornye", "lynae"} for event in transitions)
    print("manual_120s_baseline_resource_accounting_smoke_test ok")


if __name__ == "__main__":
    main()
