from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.roster import read_party_presets
from simulator.simulation import Simulation


NEW_PARTY_ID = "aemeath_mornye_lynae_enabled_test_party"
BASELINE_PARTY_ID = "aemeath_mornye_enabled_test_party"
EXPECTED_SOURCE_REF = "?\uafa6\u30092!B227"


def main() -> None:
    presets = read_party_presets(ROOT / "data")
    baseline = presets[BASELINE_PARTY_ID]
    preset = presets[NEW_PARTY_ID]
    sim = Simulation.from_json(ROOT / "data", party=NEW_PARTY_ID)

    assert preset["transition_overrides"]["characters"]["aemeath"] == baseline["transition_overrides"]["characters"]["aemeath"]
    assert preset["transition_overrides"]["characters"]["mornye"] == baseline["transition_overrides"]["characters"]["mornye"]
    assert preset["mechanic_overrides"]["aemeath"] == baseline["mechanic_overrides"]["aemeath"]
    assert preset["mechanic_overrides"]["mornye"] == baseline["mechanic_overrides"]["mornye"]
    assert preset["generic_swap"] == baseline["generic_swap"]

    lynae_transition = sim.transition_config["characters"]["lynae"]
    assert lynae_transition["intro_qte"]["enabled"] is True
    assert lynae_transition["intro_qte"]["mode"] == "enabled"
    assert lynae_transition["outro"]["enabled"] is True
    assert lynae_transition["outro"]["requires_concerto"] is True

    tune_break = sim.transition_config["mechanics"]["tune_break_system"]
    assert tune_break["mode"] == baseline["mechanic_overrides"]["tune_break_system"]["mode"]
    assert tune_break["enemy_off_tune_max"] == 3920
    assert tune_break["enemy_tune_break_cooldown_seconds"] == 3.0
    assert tune_break["enemy_tune_break_cooldown_source_ref"] == EXPECTED_SOURCE_REF
    print("aemeath_mornye_lynae_transition_config_smoke_test ok")


if __name__ == "__main__":
    main()
