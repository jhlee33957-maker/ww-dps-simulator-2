from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rl.evaluate_maskable_ppo import build_arg_parser as build_eval_parser
from rl.evaluate_maskable_ppo import build_effective_config_from_args as build_eval_config
from rl.train_maskable_ppo import build_arg_parser as build_train_parser
from rl.train_maskable_ppo import build_effective_config_from_args as build_train_config
from simulator.transition_config import get_character_transition_mode


def test_train_parser_accepts_transition_modes() -> None:
    parser = build_train_parser()
    args = parser.parse_args(
        [
            "--party",
            "aemeath_mornye_enabled_test_party",
            "--transition-mode",
            "enabled",
            "--aemeath-qte-mode",
            "dry_run",
            "--mornye-intro-mode",
            "enabled",
        ]
    )
    assert args.transition_mode == "enabled"
    assert args.aemeath_qte_mode == "dry_run"
    assert args.mornye_intro_mode == "enabled"
    config, party_preset = build_train_config(args)
    assert party_preset is not None
    assert get_character_transition_mode(config, "aemeath", "intro_qte") == "dry_run"
    assert get_character_transition_mode(config, "mornye", "intro_qte") == "enabled"
    assert "cli_override" in config["_transition_config_source"]


def test_eval_parser_accepts_transition_modes() -> None:
    parser = build_eval_parser()
    args = parser.parse_args(
        [
            "--model-path",
            "models/example.zip",
            "--transition-mode",
            "enabled",
            "--aemeath-qte-mode",
            "disabled",
            "--mornye-intro-mode",
            "dry_run",
        ]
    )
    config, party_preset = build_eval_config(args)
    assert party_preset is None
    assert get_character_transition_mode(config, "aemeath", "intro_qte") == "disabled"
    assert get_character_transition_mode(config, "mornye", "intro_qte") == "dry_run"
    assert "cli_override" in config["_transition_config_source"]


def test_no_flags_use_party_preset_or_default() -> None:
    parser = build_train_parser()
    preset_args = parser.parse_args(["--party", "aemeath_mornye_enabled_test_party"])
    preset_config, _party_preset = build_train_config(preset_args)
    assert get_character_transition_mode(preset_config, "aemeath", "intro_qte") == "enabled"
    assert get_character_transition_mode(preset_config, "mornye", "intro_qte") == "enabled"
    assert "party_preset" in preset_config["_transition_config_source"]
    assert "cli_override" not in preset_config["_transition_config_source"]

    default_args = parser.parse_args([])
    default_config, default_preset = build_train_config(default_args)
    assert default_preset is None
    assert get_character_transition_mode(default_config, "aemeath", "intro_qte") == "disabled"
    assert get_character_transition_mode(default_config, "mornye", "intro_qte") == "disabled"
    assert default_config["_transition_config_source"] == ["default"]


def main() -> None:
    test_train_parser_accepts_transition_modes()
    test_eval_parser_accepts_transition_modes()
    test_no_flags_use_party_preset_or_default()
    print("Transition mode CLI smoke test passed.")


if __name__ == "__main__":
    main()
