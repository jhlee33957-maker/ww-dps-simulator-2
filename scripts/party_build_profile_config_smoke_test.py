from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rl.train_maskable_ppo import build_arg_parser
from simulator.build_profiles import load_build_profiles, parse_build_profile_overrides, resolve_party_build_profiles
from simulator.roster import read_party_presets
from simulator.simulation import Simulation


def test_party_preset_build_profiles() -> None:
    sim = Simulation.from_json(DATA_DIR, party="aemeath_mornye_enabled_test_party")
    assert sim.active_build_profiles["aemeath"] == "liberation_focus_test"
    assert sim.active_build_profiles["mornye"] == "support_er_cap"
    assert sim.characters["mornye"].energy_regen == 2.6


def test_cli_style_override_precedence() -> None:
    party = read_party_presets(DATA_DIR)["aemeath_mornye_enabled_test_party"]
    profiles = load_build_profiles(DATA_DIR)
    resolved = resolve_party_build_profiles(
        party,
        cli_overrides={"aemeath": "default"},
        selected_character_ids=party["members"],
        build_profiles=profiles,
    )
    assert resolved["aemeath"] == "default"
    assert resolved["mornye"] == "support_er_cap"


def test_generic_cli_format_and_metadata() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["--build-profile", "aemeath:liberation_focus_test", "--build-profile", "mornye:support_er_cap"])
    assert parse_build_profile_overrides(args.build_profile) == {
        "aemeath": "liberation_focus_test",
        "mornye": "support_er_cap",
    }
    sim = Simulation.from_json(
        DATA_DIR,
        party="aemeath_mornye_enabled_test_party",
        build_profile_overrides={"aemeath": "default"},
    )
    assert sim.active_build_profiles["aemeath"] == "default"
    assert "aemeath" in sim.effective_build_stats_summary


if __name__ == "__main__":
    test_party_preset_build_profiles()
    test_cli_style_override_precedence()
    test_generic_cli_format_and_metadata()
    print("party_build_profile_config_smoke_test ok")
