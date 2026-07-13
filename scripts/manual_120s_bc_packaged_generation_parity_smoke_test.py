from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rl.demo_contract import (  # noqa: E402
    DEFAULT_DEMO_PATH,
    REQUIRED_ARRAYS,
    SOURCE_ROUTE_FILE_SHA256,
    file_sha256,
    load_demo_npz,
)
from scripts.generate_manual_120s_bc_demonstration import generate_manual_120s_bc_demonstration  # noqa: E402


def main() -> None:
    if file_sha256(ROOT / "data" / "manual_120s_baseline_routes_v104.json") != SOURCE_ROUTE_FILE_SHA256:
        raise AssertionError("source route bytes do not match the canonical raw SHA before generation parity")
    packaged = load_demo_npz(DEFAULT_DEMO_PATH)
    with tempfile.TemporaryDirectory() as temp_dir:
        generated_path = Path(temp_dir) / "manual_120s_bc_demonstration_v105.npz"
        generate_manual_120s_bc_demonstration(generated_path)
        generated = load_demo_npz(generated_path)
    assert packaged["metadata"] == generated["metadata"]
    assert packaged["metadata"]["source_route_file_sha256"] == SOURCE_ROUTE_FILE_SHA256
    for name in REQUIRED_ARRAYS:
        packaged_array = np.asarray(packaged[name])
        generated_array = np.asarray(generated[name])
        assert packaged_array.dtype == generated_array.dtype, name
        assert packaged_array.shape == generated_array.shape, name
        assert np.array_equal(packaged_array, generated_array), name
    print("manual_120s_bc_packaged_generation_parity_smoke_test ok")


if __name__ == "__main__":
    main()
