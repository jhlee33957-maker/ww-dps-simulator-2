from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from search.mcts_reporting import comparison_for_completed_route


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    route = {"route_id": "mcts_fixture", "total_damage": 5600000.0, "dps": 46666.666666666664, "selected_sequence_sha256": "f" * 64}
    source = root / "results/beam_search_v114_completed_v116/result_manifest.json"
    with tempfile.TemporaryDirectory(prefix="mcts-reporting-integrity-") as tmp:
        fixture = Path(tmp)
        target = fixture / "results/beam_search_v114_completed_v116/result_manifest.json"
        target.parent.mkdir(parents=True)
        target.write_bytes(source.read_bytes())
        comparison = comparison_for_completed_route(route, root=fixture)
        assert comparison["status"] == "available"
        assert comparison["overall_project_winner"]["kind"] == "beam_search_route"
        assert comparison["overall_project_winner"]["route_id"] == "67a4250b3b8d0de9"
        assert comparison["global_optimum_proven"] is False

        original = target.read_bytes()
        target.unlink()
        missing = comparison_for_completed_route(route, root=fixture)
        assert missing["status"] == "unavailable" and missing["search_result_valid"] is True
        assert "overall_project_winner" not in missing

        target.write_bytes(original + b"\n")
        tampered = comparison_for_completed_route(route, root=fixture)
        assert tampered["status"] == "unavailable" and tampered["search_result_valid"] is True
        assert "integrity error" in tampered["reason"]
        assert tampered["expected_sha256"] == "247f2a912d05bd4d89a3a7bbcb16c0877515427a8b46f7dc1795501b255b03ef"
        assert tampered["actual_sha256"] != tampered["expected_sha256"]
        assert "overall_project_winner" not in tampered
    print("mcts_reporting_current_winner_smoke_test ok valid_missing_tampered=true")


if __name__ == "__main__": main()
