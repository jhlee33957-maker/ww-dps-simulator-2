from __future__ import annotations

import numpy as np

from simulator.action_executor import is_action_valid
from simulator.simulation import Simulation


def action_mask(simulation: Simulation) -> np.ndarray:
    return np.array(
        [is_action_valid(action, simulation.state)[0] for action in simulation.actions.values()],
        dtype=bool,
    )
