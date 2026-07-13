from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mornye_syntony_field_heal_scheduler_smoke_test import main


if __name__ == "__main__":
    main()
