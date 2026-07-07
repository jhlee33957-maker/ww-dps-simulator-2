from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
REFERENCE_PATH = ROOT / "data" / "mechanics" / "aemeath_mechanics.json"

CANONICAL_LABELS = ("强化E-震谐", "强化E-震谐增幅")
MOJIBAKE_FRAGMENTS = ("凉", "뷴", "뙑", "罌", "욃", "퉭")


def read_utf8(path: Path) -> str:
    raw = path.read_bytes()
    return raw.decode("utf-8")


def main() -> None:
    texts = {
        CONFIG_PATH: read_utf8(CONFIG_PATH),
        REFERENCE_PATH: read_utf8(REFERENCE_PATH),
    }
    for path, text in texts.items():
        for label in CANONICAL_LABELS:
            assert label in text, f"{path} missing canonical label {label}"
        for fragment in MOJIBAKE_FRAGMENTS:
            assert fragment not in text, f"{path} still contains mojibake fragment {fragment}"
        json.loads(text)

    config = json.loads(texts[CONFIG_PATH])
    followups = {
        entry["variant"]: entry
        for entry in config["modes"]["tune_rupture"]["seraphic_duet_followups"]
    }
    normal = followups["normal"]
    enhanced = followups["enhanced"]
    assert normal["label"] == "强化E-震谐"
    assert normal["tune_multiplier"] == 1.0935
    assert normal["repeat_count"] == 5
    assert normal["formula_type"] == "tune_response"
    assert normal["source_status"] == "workbook_confirmed"

    assert enhanced["label"] == "强化E-震谐增幅"
    assert enhanced["tune_multiplier"] == 1.0935
    assert enhanced["repeat_count"] == 10
    assert enhanced["formula_type"] == "tune_response"
    assert enhanced["source_status"] == "workbook_confirmed"
    print("aemeath_forte_label_encoding_smoke_test ok")


if __name__ == "__main__":
    main()
