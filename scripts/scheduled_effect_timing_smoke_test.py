from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.scheduled_effect_activation_time_smoke_test import main


if __name__ == "__main__":
    main()
