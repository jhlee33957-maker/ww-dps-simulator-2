from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MECHANICS = ROOT / "data" / "mechanics" / "aemeath_mechanics.json"
FORTE = ROOT / "data" / "character_mechanic_effects" / "aemeath_forte_circuit.json"
PROGRESS = ROOT / "PROJECT_PROGRESS_STATE.json"
FILES = [MECHANICS, FORTE, PROGRESS]
OVERDRIVE_LABEL = "\u5927\u62db1"
GOOD_DAMAGE_REFS = ["dmg!2578", "dmg!2579", "dmg!2628", "dmg!2629"]
BAD_DAMAGE_REFS = [
    "dmg/\u9c32\u54aa\u06ef\u062f\u4e5f\ucfcfamageData!2578",
    "dmg/\u9c32\u54aa\u06ef\u062f\u4e5f\ucfcfamageData!2579",
    "dmg/\u9c32\u54aa\u06ef\u062f\u4e5f\ucfcfamageData!2628",
    "dmg/\u9c32\u54aa\u06ef\u062f\u4e5f\ucfcfamageData!2629",
    "dmg/",
    "DamageData!2578",
    "DamageData!2579",
    "DamageData!2628",
    "DamageData!2629",
]
BAD_ENCODING_FRAGMENTS = ["???1", "???", "\ufffd", "\u5360?"]


def read_utf8(path: Path) -> str:
    data = path.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), path
    return data.decode("utf-8")


def collect_c0_text(mechanics: dict, forte: dict) -> str:
    texts: list[str] = []
    texts.extend(mechanics.get("scope", {}).get("included", []))
    for state in mechanics.get("states", []):
        if state.get("name") in {"Trail No-cost", "Forte Enhancement"}:
            texts.append(state.get("name", ""))
            texts.extend(state.get("modeled_behavior", []))
    texts.extend(mechanics.get("forte_circuit", {}).get("modeled_behavior", []))
    texts.extend(mechanics.get("rupturous_trail", {}).get("modeled_behavior", []))
    for entry in mechanics.get("seraphic_duet", []):
        texts.append(entry.get("name", ""))
        texts.extend(entry.get("modeled_behavior", []))
    rupturous = forte["modes"]["tune_rupture"]["rupturous_trail"]
    for key, value in rupturous.items():
        if key != "source_refs":
            texts.append(str(value))
    return "\n".join(texts).lower()


def trail_no_cost_text(mechanics: dict) -> str:
    for state in mechanics.get("states", []):
        if state.get("name") == "Trail No-cost":
            return "\n".join(state.get("modeled_behavior", []))
    raise AssertionError("Trail No-cost state not found")


def main() -> None:
    assert [ord(c) for c in OVERDRIVE_LABEL] == [0x5927, 0x62DB, 0x0031]
    texts = {path: read_utf8(path) for path in FILES}
    combined_text = "\n".join(texts.values())
    assert not any(fragment in combined_text for fragment in BAD_ENCODING_FRAGMENTS), combined_text

    mechanics = json.loads(texts[MECHANICS])
    forte = json.loads(texts[FORTE])
    json.loads(texts[PROGRESS])
    trail_text = trail_no_cost_text(mechanics)
    assert OVERDRIVE_LABEL in texts[MECHANICS]
    assert f"Granted by Overdrive / {OVERDRIVE_LABEL} for 30 seconds." in trail_text

    metadata_text = texts[MECHANICS] + "\n" + texts[FORTE]
    assert all(ref in metadata_text for ref in GOOD_DAMAGE_REFS), metadata_text
    assert not any(ref in metadata_text for ref in BAD_DAMAGE_REFS), metadata_text

    c0_text = collect_c0_text(mechanics, forte)
    stale_phrases = [
        "scaffold",
        "scaffolding",
        "scaffold_only",
        "unresolved s0 trail removal",
        "unresolved runtime damage gate",
        "maximum stacks 5",
        "application unresolved",
        "consumption unresolved",
    ]
    assert not any(phrase in c0_text for phrase in stale_phrases), c0_text
    assert "Fusion Trail" in texts[MECHANICS]
    assert "C6" in texts[MECHANICS]
    assert "multi-target" in texts[MECHANICS]
    print("aemeath_rupturous_trail_metadata_utf8_guard_smoke_test ok")


if __name__ == "__main__":
    main()
