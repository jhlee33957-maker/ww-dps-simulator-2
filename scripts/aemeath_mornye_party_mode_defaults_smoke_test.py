from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(ROOT))

from rl.evaluate_maskable_ppo import build_arg_parser as build_eval_parser
from rl.evaluate_maskable_ppo import build_effective_config_from_args as build_eval_config
from rl.train_maskable_ppo import build_arg_parser as build_train_parser
from rl.train_maskable_ppo import build_effective_config_from_args as build_train_config
from simulator.mechanic_events import SUPPORTED_AEMEATH_RESONANCE_MODES
from simulator.roster import read_party_presets
from simulator.simulation import Simulation
from simulator.transition_config import mechanics_mode_summary


PARTY_ID = "aemeath_mornye_test_party"
EXPECTED_AEMEATH_MODE = "tune_rupture"
EXPECTED_MORNYE_HEAL_MODE = "simplified_syntony_field_uptime"


def test_party_preset_defaults() -> None:
    presets = read_party_presets(DATA_DIR)
    assert PARTY_ID in presets
    party = presets[PARTY_ID]
    overrides = party["mechanic_overrides"]
    assert overrides["aemeath"]["aemeath_resonance_mode"] == EXPECTED_AEMEATH_MODE
    assert overrides["aemeath"]["aemeath_resonance_mode_source"] == "party_preset"
    assert overrides["mornye"]["mornye_heal_event_mode"] == EXPECTED_MORNYE_HEAL_MODE
    assert overrides["mornye"]["mornye_heal_event_mode_source"] == "party_preset"

    sim = Simulation.from_json(DATA_DIR, party=PARTY_ID)
    summary = sim.summary()
    assert summary.selected_party_id == PARTY_ID
    assert summary.aemeath_resonance_mode == EXPECTED_AEMEATH_MODE
    assert summary.aemeath_resonance_mode_source == "party_preset"
    assert summary.mornye_heal_event_mode == EXPECTED_MORNYE_HEAL_MODE
    assert summary.mornye_heal_event_mode_source == "party_preset"
    assert summary.active_party_build_profiles == {"mornye": "default", "aemeath": "default"}


def test_modes_remain_configurable() -> None:
    assert "fusion_burst" in SUPPORTED_AEMEATH_RESONANCE_MODES
    assert "tune_rupture" in SUPPORTED_AEMEATH_RESONANCE_MODES

    train_parser = build_train_parser()
    train_args = train_parser.parse_args(
        [
            "--party",
            PARTY_ID,
            "--aemeath-resonance-mode",
            "fusion_burst",
            "--mornye-heal-event-mode",
            "field_creation_only",
        ]
    )
    train_config, party_preset = build_train_config(train_args)
    train_modes = mechanics_mode_summary(train_config)
    assert party_preset is not None
    assert train_modes["aemeath"]["aemeath_resonance_mode"] == "fusion_burst"
    assert train_modes["aemeath"]["aemeath_resonance_mode_source"] == "cli_override"
    assert train_modes["mornye"]["heal_event_mode"] == "field_creation_only"
    assert train_modes["mornye"]["heal_event_mode_source"] == "cli_override"

    eval_parser = build_eval_parser()
    eval_args = eval_parser.parse_args(
        [
            "--model-path",
            "models/example.zip",
            "--party",
            PARTY_ID,
            "--aemeath-resonance-mode",
            "fusion_burst",
            "--mornye-heal-event-mode",
            "disabled",
        ]
    )
    eval_config, _eval_party = build_eval_config(eval_args)
    eval_modes = mechanics_mode_summary(eval_config)
    assert eval_modes["aemeath"]["aemeath_resonance_mode"] == "fusion_burst"
    assert eval_modes["aemeath"]["aemeath_resonance_mode_source"] == "cli_override"
    assert eval_modes["mornye"]["heal_event_mode"] == "disabled"
    assert eval_modes["mornye"]["heal_event_mode_source"] == "cli_override"


def test_non_mornye_parties_are_not_forced_to_tune_rupture() -> None:
    solo = Simulation.from_json(DATA_DIR, party="aemeath")
    solo_summary = solo.summary()
    assert solo_summary.aemeath_resonance_mode != "tune_rupture"
    assert solo_summary.aemeath_resonance_mode == "unresolved"
    assert solo_summary.aemeath_resonance_mode_source == "default"

    aemeath_test_party = Simulation.from_json(DATA_DIR, party="aemeath_test_party")
    test_summary = aemeath_test_party.summary()
    assert test_summary.aemeath_resonance_mode == "unresolved"
    assert test_summary.aemeath_resonance_mode_source == "default"


def main() -> None:
    test_party_preset_defaults()
    test_modes_remain_configurable()
    test_non_mornye_parties_are_not_forced_to_tune_rupture()
    print("aemeath_mornye_party_mode_defaults_smoke_test ok")


if __name__ == "__main__":
    main()
