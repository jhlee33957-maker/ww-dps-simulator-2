from __future__ import annotations

import numpy as np

from simulator.simulation import Simulation


def action_mask(simulation: Simulation) -> np.ndarray:
    return np.array(
        [
            simulation.is_action_available(action)
            for action in simulation.actions.values()
            if action.policy_selectable
        ],
        dtype=bool,
    )
