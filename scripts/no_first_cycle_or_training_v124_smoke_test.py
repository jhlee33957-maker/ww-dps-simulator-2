from __future__ import annotations

from v124_timing_test_support import ROOT


def main() -> None:
    candidates = [
        ROOT / "data" / "account_first_cycle_route_v124.json",
        *list((ROOT / "results").glob("account_first_cycle*")),
        *list((ROOT / "results").glob("*v124*")),
        *list((ROOT / "models").glob("*v124*")),
        *list(ROOT.glob("ww-dps-simulator-2-124*.zip")),
    ]
    forbidden = [path for path in candidates if path.exists()]
    assert not forbidden, [str(path) for path in forbidden]
    print("no_first_cycle_or_training_v124_smoke_test ok")


if __name__ == "__main__":
    main()
