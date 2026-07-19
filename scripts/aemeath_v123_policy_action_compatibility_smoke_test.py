from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aemeath_v123_test_utils import make_account_sim
from rl.demo_contract import party_config_hash
from simulator.account_config_contract import account_config_hash


EXPECTED_POLICY_ORDER = [
    "mornye_basic_attack", "mornye_heavy_attack", "mornye_resonance_skill", "mornye_resonance_liberation", "mornye_tune_break",
    "swap_to_aemeath", "aemeath_basic_attack", "aemeath_resonance_skill", "aemeath_heavy_attack", "aemeath_resonance_liberation",
    "aemeath_tune_break", "short_wait", "lynae_basic_attack", "lynae_spark_collision", "lynae_resonance_skill",
    "lynae_resonance_liberation", "lynae_echo_hyvatia", "lynae_tune_break", "lynae_polychrome_leap", "lynae_visual_impact",
    "lynae_iridescent_splash", "swap_to_mornye", "swap_to_lynae", "mornye_echo_reactor_husk", "aemeath_echo_sigillum",
]


def main() -> None:
    simulation = make_account_sim()
    assert simulation.get_policy_action_ids() == EXPECTED_POLICY_ORDER
    assert len(simulation.get_policy_action_ids()) == 25
    assert party_config_hash(root=ROOT) == "a6a98f0aeb16adf8176b3c4383aa0441b5d28c6276f7e91006414820d0214d6d"
    assert account_config_hash(ROOT) == "a4cc5fcf0f3d5074af0a740944dfe12f89c2e0535a768b818319bf56fc2f0bca"
    assert hashlib.sha256((ROOT / "data/account_party_presets_v122.json").read_bytes()).hexdigest() == "105baff5fd7de567e93ab892e3e2983652022a794434e9dbff08b75acb216346"
    assert hashlib.sha256((ROOT / "data/account_content_start_v122.json").read_bytes()).hexdigest() == "733348695ae784c31e02bd6d36cafb35b95440e8fade4e8f567f1e3a440b214b"
    print("aemeath_v123_policy_action_compatibility_smoke_test ok policy_count=25")


if __name__ == "__main__":
    main()
