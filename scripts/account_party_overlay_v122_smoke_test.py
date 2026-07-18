from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator.roster import read_party_presets

PARTY_ID = "aemeath_mornye_lynae_account_actual_01"
BASE_PARTY_SHA256 = "d7371f8a1b2a7317326890ad0a123a9fe6d3beb8323477d8e8d52cbf69266947"


def main() -> None:
    base_path = ROOT / "data/party_presets.json"
    assert __import__("hashlib").sha256(base_path.read_bytes()).hexdigest() == BASE_PARTY_SHA256
    base_before = json.loads(base_path.read_text(encoding="utf-8-sig"))
    merged = read_party_presets(ROOT / "data")
    assert PARTY_ID in merged
    assert PARTY_ID not in {item["party_id"] for item in base_before}
    assert json.loads(base_path.read_text(encoding="utf-8-sig")) == base_before
    assert merged["aemeath_mornye_lynae_enabled_test_party"] == next(
        item for item in base_before if item["party_id"] == "aemeath_mornye_lynae_enabled_test_party"
    )
    merged[PARTY_ID]["members"].append("mutated")
    assert "mutated" not in read_party_presets(ROOT / "data")[PARTY_ID]["members"]

    with tempfile.TemporaryDirectory() as temp:
        data = Path(temp)
        shutil.copy2(base_path, data / "party_presets.json")
        (data / "account_party_presets_v122.json").write_text(
            json.dumps({"parties": [{"party_id": "aemeath", "members": []}]}), encoding="utf-8"
        )
        try:
            read_party_presets(data)
        except ValueError as exc:
            assert "add only new party IDs" in str(exc)
        else:
            raise AssertionError("overlay collision unexpectedly passed")
        (data / "account_party_presets_v122.json").write_text(
            json.dumps({"parties": [{"party_id": "duplicate"}, {"party_id": "duplicate"}]}), encoding="utf-8"
        )
        try:
            read_party_presets(data)
        except ValueError as exc:
            assert "Duplicate account party overlay ID" in str(exc)
        else:
            raise AssertionError("duplicate overlay ID unexpectedly passed")
    print("account_party_overlay_v122_smoke_test ok")


if __name__ == "__main__":
    main()
