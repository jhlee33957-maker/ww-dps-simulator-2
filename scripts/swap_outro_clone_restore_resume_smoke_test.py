from __future__ import annotations

from v114_test_support import build, outro_instances, set_concerto, value
from search.beam_state import (
    clone_simulation_for_search,
    future_state_fingerprint,
    restore_simulation_from_state,
    serialize_simulation_state,
)


def main() -> None:
    sim = build()
    set_concerto(sim, "aemeath")
    assert sim.execute_action("swap_to_mornye")
    sim.state.cooldowns["swap_reentry:lynae"] = 0.75
    expected = future_state_fingerprint(sim)
    clone = clone_simulation_for_search(sim)
    restored = restore_simulation_from_state(build(), serialize_simulation_state(sim))
    for candidate in (clone, restored):
        assert future_state_fingerprint(candidate) == expected
        assert candidate.state.cooldowns["swap_reentry:lynae"] == 0.75
        instances = outro_instances(candidate)
        assert set(instances) == {"mornye", "lynae"}
        assert value(instances["mornye"]) == value(instances["lynae"]) == 0.1
    print("swap_outro_clone_restore_resume_smoke_test ok")


if __name__ == "__main__":
    main()
