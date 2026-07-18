from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulator.account_constellation_effects import aemeath_s5_unsupported_effects, unsupported_constellation_effects


def main() -> None:
    result = aemeath_s5_unsupported_effects()
    assert result["implemented"] is False
    assert result["runtime_value"] == 0.0
    assert "aemeath_s5_all_effects" in result["unsupported_effects"]
    assert "aemeath_s5_all_effects" in unsupported_constellation_effects()
    print("aemeath_s5_unsupported_v121_smoke_test ok")


if __name__ == "__main__":
    main()
