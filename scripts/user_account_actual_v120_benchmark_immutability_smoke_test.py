from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXPECTED_OBJECT_HASHES = {
    "aemeath_user_real_01": "6ab11994a6c32e6850786f99fa836205ad29db6a242e3c6d461b04fffdfa897d",
    "lynae_user_real_01": "3fbcf701bfe6ac5501d9ef0f58c09ce8bb590219800f1490ebee8c675b213316",
    "mornye_user_real_01": "19d050131fcab718630c9c302a098aec37048292a2a4f1300c3e77103d0d7c82",
    "aemeath_mornye_lynae_enabled_test_party": "13d28350df0229bab49d22427fa6171a3aa2c245a467d605768aab5dfdadedfb",
}
EXPECTED_FILE_HASHES = {
    "results/beam_search_v114_completed_v116/winning_route_summary.json": (
        "3565ab1c1beff51f5af06cdd20a889e12216c0952393c845586936bda9aa1f15"
    ),
    "results/manual_120s_baseline_v114_summary.json": (
        "16da6d9b35734189568190b09b398064dc93ab843425709773dfb8280979038f"
    ),
}


def object_hash(value: object) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    build_profiles = json.loads((ROOT / "data" / "build_profiles.json").read_text(encoding="utf-8-sig"))
    parties = json.loads((ROOT / "data" / "party_presets.json").read_text(encoding="utf-8-sig"))
    objects = {
        "aemeath_user_real_01": build_profiles["profiles"]["aemeath"]["aemeath_user_real_01"],
        "lynae_user_real_01": build_profiles["profiles"]["lynae"]["lynae_user_real_01"],
        "mornye_user_real_01": build_profiles["profiles"]["mornye"]["mornye_user_real_01"],
        "aemeath_mornye_lynae_enabled_test_party": next(
            item for item in parties if item["party_id"] == "aemeath_mornye_lynae_enabled_test_party"
        ),
    }
    for name, expected in EXPECTED_OBJECT_HASHES.items():
        assert object_hash(objects[name]) == expected, name

    assert objects["mornye_user_real_01"]["weapon"]["weapon_id"] == "discord"
    assert objects["mornye_user_real_01"]["weapon"]["rank"] == 5

    for rel, expected in EXPECTED_FILE_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel

    print("user_account_actual_v120_benchmark_immutability_smoke_test ok")


if __name__ == "__main__":
    main()
