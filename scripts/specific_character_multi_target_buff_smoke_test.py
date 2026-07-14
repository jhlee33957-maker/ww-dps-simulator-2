from __future__ import annotations

from v114_test_support import OUTRO_BUFF_ID, build
from simulator.buff_system import apply_buff


def main() -> None:
    sim = build()
    canonical = sim.buffs[OUTRO_BUFF_ID]
    for target, dynamic in (("mornye", 0.1), ("lynae", 0.2)):
        runtime = canonical.model_copy(deep=True)
        runtime.target_character_id = target
        runtime.metadata = {**runtime.metadata, "dynamic_value": dynamic}
        apply_buff(sim.state, runtime, "aemeath")
    matches = [b for b in sim.state.active_buffs if b.buff_id == OUTRO_BUFF_ID]
    assert len(matches) == 2
    runtime = canonical.model_copy(deep=True)
    runtime.target_character_id = "mornye"
    runtime.metadata = {**runtime.metadata, "dynamic_value": 0.2}
    apply_buff(sim.state, runtime, "aemeath")
    matches = [b for b in sim.state.active_buffs if b.buff_id == OUTRO_BUFF_ID]
    assert len(matches) == 2
    assert {b.target_character_id: b.metadata["dynamic_value"] for b in matches} == {"mornye": 0.2, "lynae": 0.2}
    print("specific_character_multi_target_buff_smoke_test ok")


if __name__ == "__main__":
    main()
