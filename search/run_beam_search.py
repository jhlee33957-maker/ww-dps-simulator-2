from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.beam_search import compact_cli_summary, parse_and_validate_args, run_search_from_args  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_and_validate_args(argv)
    result = run_search_from_args(args)
    if args.dry_run_plan:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(compact_cli_summary(result), separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
