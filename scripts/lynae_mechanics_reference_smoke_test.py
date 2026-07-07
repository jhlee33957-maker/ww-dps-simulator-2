from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BAD_FRAGMENTS = ["?녑쪎", "?뉓컧?띶틪", "?깁르與", "繹℡쉘", "役곩뀎", "?ц돯"]


def main() -> None:
    path = ROOT / "data/mechanics/lynae_mechanics.json"
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["implemented"]
    assert data["simplified"]
    assert data["source_references"]
    assert data["source_name"] == "琳奈"
    assert data["implemented"]["spectral_analysis"]["source_label"] == "震谐响应"
    for fragment in BAD_FRAGMENTS:
        assert fragment not in text
    print("lynae_mechanics_reference_smoke_test ok")


if __name__ == "__main__":
    main()
