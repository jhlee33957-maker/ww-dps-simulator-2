from __future__ import annotations

import copy
from dataclasses import dataclass

from simulator.models import TimelineEntry
from simulator.simulation import Simulation


@dataclass(slots=True)
class BeamCandidate:
    simulation: Simulation
    action_sequence: list[str]
    score: float


@dataclass(slots=True)
class BeamSearchResult:
    total_damage: float
    dps: float
    final_time: float
    action_sequence: list[str]
    timeline: list[TimelineEntry]
    explored_nodes: int
    simulation: Simulation


def run_beam_search(
    initial_simulation: Simulation,
    beam_width: int = 20,
    max_steps: int = 100,
    use_heuristic_score: bool = False,
) -> BeamSearchResult:
    beam_width = max(1, beam_width)
    max_steps = max(1, max_steps)
    initial = copy.deepcopy(initial_simulation)
    beam = [
        BeamCandidate(
            simulation=initial,
            action_sequence=[],
            score=_score(initial, use_heuristic_score),
        )
    ]
    explored_nodes = 0

    for _ in range(max_steps):
        if all(candidate.simulation.state.current_time >= candidate.simulation.combat_duration for candidate in beam):
            break

        next_candidates: list[BeamCandidate] = []
        for candidate in beam:
            sim = candidate.simulation
            if sim.state.current_time >= sim.combat_duration:
                next_candidates.append(candidate)
                continue

            for action_id in sim.valid_action_ids():
                next_sim = copy.deepcopy(sim)
                if not next_sim.execute_action(action_id):
                    continue
                explored_nodes += 1
                next_candidates.append(
                    BeamCandidate(
                        simulation=next_sim,
                        action_sequence=[*candidate.action_sequence, action_id],
                        score=_score(next_sim, use_heuristic_score),
                    )
                )

        if not next_candidates:
            break

        next_candidates.sort(key=lambda item: item.score, reverse=True)
        beam = next_candidates[:beam_width]

    best = max(beam, key=lambda item: item.simulation.state.total_damage)
    summary = best.simulation.summary()
    return BeamSearchResult(
        total_damage=summary.total_damage,
        dps=summary.dps,
        final_time=summary.final_time,
        action_sequence=best.action_sequence,
        timeline=summary.timeline,
        explored_nodes=explored_nodes,
        simulation=best.simulation,
    )


def _score(simulation: Simulation, use_heuristic_score: bool = False) -> float:
    if not use_heuristic_score:
        return simulation.state.total_damage

    state = simulation.state
    resource_value = 0.0
    wasted_penalty = 0.0
    for character_id in simulation.characters:
        resource_value += state.resonance_energy.get(character_id, 0.0) * 10.0
        resource_value += state.concerto_energy.get(character_id, 0.0) * 2.0
        wasted_penalty += state.wasted_resonance_energy.get(character_id, 0.0) * 8.0
        wasted_penalty += state.wasted_concerto_energy.get(character_id, 0.0) * 1.0

    overrun = max(0.0, state.current_time - simulation.combat_duration)
    return state.total_damage + resource_value - wasted_penalty - overrun * 100.0
