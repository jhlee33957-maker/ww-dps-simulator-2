from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import lynae_s2_apply_outro_buff, lynae_s2_outro_after_switch


def main() -> None:
    buff = lynae_s2_apply_outro_buff(now=4.0, source_character_id="lynae", target_character_id="aemeath")
    assert buff["active"] is True
    assert buff["expires_at"] == 18.0
    assert buff["general_all_damage_deepen_total"] == 0.40
    assert buff["liberation_total_deepen"] == 0.65
    assert lynae_s2_outro_after_switch(buff, "aemeath")["active"] is True
    cleared = lynae_s2_outro_after_switch(buff, "mornye")
    assert cleared["active"] is False
    assert cleared["ended_early_by_switch"] is True
    print("lynae_s2_outro_early_end_v121_smoke_test ok")


if __name__ == "__main__":
    main()
