from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from account_constellation_source_workbook_v121 import load_source_cache, source_references


def main() -> None:
    source = json.loads((ROOT / "data/source/user_account_constellation_single_boss_v121.json").read_text(encoding="utf-8"))
    started = time.perf_counter()
    cache = load_source_cache(source)
    elapsed = time.perf_counter() - started
    try:
        import resource

        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        peak_rss = None
    assert elapsed < 180.0, elapsed
    print(
        "account_constellation_v121_source_audit_runtime_bound_smoke_test ok "
        f"references={len(source_references(source))} sheets={cache.sheet_count} cells={cache.cell_count} "
        f"elapsed_seconds={elapsed:.3f} peak_rss={peak_rss}"
    )


if __name__ == "__main__":
    main()
