from __future__ import annotations

import numpy as np

from simulator.simulation import Simulation


def action_mask(simulation: Simulation) -> np.ndarray:
    valid_ids = set(simulation.valid_action_ids())
    return np.array(
        [action_id in valid_ids for action_id in simulation.actions],
        dtype=bool,
    )
