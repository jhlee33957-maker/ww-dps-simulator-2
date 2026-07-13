from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
NPZ_PATH = ROOT / "data" / "generated" / "manual_120s_bc_demonstration_v105.npz"
EXPECTED_ROUTE_SHA256 = "c510204b78fc547e2ba1224e82193cbaf43728d9a4107eb1090b6ebaab59a90a"


def main() -> None:
    with np.load(NPZ_PATH, allow_pickle=False) as data:
        metadata = json.loads(str(np.asarray(data["metadata_json"]).item()))
    assert metadata["source_route_file_sha256"] == EXPECTED_ROUTE_SHA256
    print("final_archive_dataset_metadata_suite ok")


if __name__ == "__main__":
    main()
