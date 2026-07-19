from __future__ import annotations

import json
from v124_timing_test_support import ROOT


def main() -> None:
    report = json.loads((ROOT / "reports" / "timing_markov_state_observation_audit_v124.json").read_text(encoding="utf-8"))
    assert report["observation_v6_shape"] == 330
    assert report["observation_v6_modified"] is False
    assert report["training_allowed_under_v6_after_timing_patch"] is False
    assert report["observation_v7_required"] is True
    assert report["markov_aliasing_found"] is True
    assert len(report["hidden_future_affecting_state_not_derivable"]) >= 12
    assert report["raw_unbounded_packet_arrays_recommended"] is False
    print("timing_markov_state_observation_audit_v124_smoke_test ok")


if __name__ == "__main__":
    main()

