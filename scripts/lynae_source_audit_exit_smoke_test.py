from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/lynae_source_audit.py")],
        cwd=ROOT,
        timeout=60,
        capture_output=True,
        text=True,
    )
    output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.returncode == 0, output
    assert "lynae_source_audit ok" in result.stdout, output

    json_path = ROOT / "data/extracted/lynae_source_audit.json"
    report_path = ROOT / "reports/lynae_source_audit.md"
    assert json_path.exists(), output
    assert report_path.exists(), output

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["source_name"] == "琳奈", output
    assert data["passive_buff_candidates"]["row_range"] == "2553:2635", output
    assert abs(data["spectral_analysis"]["derived_multiplier"] - 18.8075) < 1e-9, output
    assert data["spectral_analysis_c2"]["implementation_status"] == (
        "constellation_gated_disabled_by_default"
    ), output
    print("lynae_source_audit_exit_smoke_test ok")


if __name__ == "__main__":
    main()
