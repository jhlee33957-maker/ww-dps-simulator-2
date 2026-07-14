from __future__ import annotations

from typing import Any


def performance_accounting(
    *,
    cumulative_expansions: int,
    invocation_start_expansions: int,
    invocation_elapsed_seconds: float,
    prior_cumulative_elapsed_seconds: float = 0.0,
    cumulative_accounting_complete: bool = True,
) -> dict[str, Any]:
    """Return unambiguous invocation and cumulative Beam performance metrics."""
    cumulative_expansions = int(cumulative_expansions)
    invocation_start_expansions = int(invocation_start_expansions)
    invocation_elapsed_seconds = float(invocation_elapsed_seconds)
    prior_cumulative_elapsed_seconds = float(prior_cumulative_elapsed_seconds)
    invocation_expansions = cumulative_expansions - invocation_start_expansions
    if invocation_expansions < 0:
        raise ValueError("Invocation start expansions exceed cumulative expansions")
    if invocation_elapsed_seconds < 0 or prior_cumulative_elapsed_seconds < 0:
        raise ValueError("Elapsed seconds cannot be negative")
    invocation_rate = (
        invocation_expansions / invocation_elapsed_seconds
        if invocation_elapsed_seconds > 0
        else None
    )
    cumulative_elapsed = (
        prior_cumulative_elapsed_seconds + invocation_elapsed_seconds
        if cumulative_accounting_complete
        else None
    )
    cumulative_rate = (
        cumulative_expansions / cumulative_elapsed
        if cumulative_elapsed is not None and cumulative_elapsed > 0
        else None
    )
    return {
        "performance_accounting_schema": "beam_search_performance_accounting_v116",
        "invocation_start_expansions": invocation_start_expansions,
        "invocation_expansions": invocation_expansions,
        "invocation_elapsed_seconds": invocation_elapsed_seconds,
        "invocation_expansions_per_second": invocation_rate,
        "prior_cumulative_elapsed_seconds": (
            prior_cumulative_elapsed_seconds if cumulative_accounting_complete else None
        ),
        "cumulative_elapsed_seconds": cumulative_elapsed,
        "cumulative_expansions_per_second": cumulative_rate,
        "cumulative_accounting_complete": bool(cumulative_accounting_complete),
        "elapsed_seconds": invocation_elapsed_seconds,
        "elapsed_seconds_semantics": "deprecated_alias_of_invocation_elapsed_seconds",
        "expansions_per_second": invocation_rate,
        "expansions_per_second_semantics": "deprecated_alias_of_invocation_expansions_per_second",
    }


def migrate_prior_accounting(state: dict[str, Any]) -> tuple[float, bool]:
    """Migrate prior elapsed time without fabricating data absent from old manifests."""
    cumulative = state.get("cumulative_elapsed_seconds")
    if cumulative is not None:
        return float(cumulative), bool(state.get("cumulative_accounting_complete", True))
    legacy = state.get("elapsed_seconds")
    if legacy is not None:
        return float(legacy), True
    return 0.0, int(state.get("expansions", 0)) == 0
