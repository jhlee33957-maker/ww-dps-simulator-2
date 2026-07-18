from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    forbidden = []
    for relative in ("results", "models", "data/generated", "reports"):
        path = ROOT / relative
        forbidden.extend(item for item in path.rglob("*123*") if item.is_file())
    assert not forbidden, f"candidate-123 baseline/search artifacts found: {forbidden}"
    assert not (ROOT / "data/manual_120s_baseline_routes_v123.json").exists()
    assert not (ROOT / "results/manual_120s_baseline_v123_summary.json").exists()
    print("aemeath_v123_no_baseline_search_artifacts_smoke_test ok")


if __name__ == "__main__":
    main()
