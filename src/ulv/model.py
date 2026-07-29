"""Core data model.

A `Dataset` mirrors ASV's publish-time semantics (see
development/architecture.md): ordered revisions, environments as factor
dicts, benchmarks with parameter axes, and result series keyed by
(benchmark, environment, revision). Input plugins build datasets; output
generators consume them. Instances are frozen: loaders construct them
fully formed and everything downstream can share them safely.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Revision:
    """One point on the history axis (typically a commit).

    `branches` lists every configured branch containing the commit —
    like asv, a result is attributed to (and graphed on) each of them.
    `branch` is the single label used by input formats whose metadata
    names exactly one branch per point (e.g. BMF sidecar files).
    """

    id: str
    commit_hash: str | None = None
    date: dt.datetime | None = None
    branch: str | None = None
    branches: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Environment:
    """Where results were produced, described as independent factors.

    Factors are the site's filter axes: machine, python, requirement
    versions, env vars for ASV; testbed (or user-decomposed factors) for
    Bencher. `extra` preserves loader fields no factor consumes, so input
    formats map losslessly.
    """

    id: str
    factors: Mapping[str, str] = field(default_factory=dict)
    extra: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Benchmark:
    """A measured quantity, optionally parameterized.

    `params` holds, per entry of `param_names`, the tuple of values that
    axis takes — the same shape ASV's `benchmarks.json` uses.
    """

    name: str
    unit: str | None = None
    type: str | None = None
    param_names: tuple[str, ...] = ()
    params: tuple[tuple[str, ...], ...] = ()
    pretty_name: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if len(self.param_names) != len(self.params):
            raise ValueError(
                f"benchmark {self.name!r}: {len(self.param_names)} param names "
                f"but {len(self.params)} param value axes"
            )


@dataclass(frozen=True)
class ResultPoint:
    """One measurement.

    `value` is a scalar for plain benchmarks or a sequence (one entry per
    parameter combination) for parameterized ones; `None` marks a failed
    or missing run. `lower`/`upper` carry BMF-style bounds and stay `None`
    when absent — absence is not zero.
    """

    value: object
    lower: float | None = None
    upper: float | None = None
    # A single mapping for scalar benchmarks; a tuple with one entry (or
    # None) per parameter combination for parameterized ones.
    stats: Mapping[str, object] | tuple[Mapping[str, object] | None, ...] | None = None
    extra: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultSeries:
    """All points for one (benchmark, environment) pair, keyed by revision id."""

    benchmark: str
    environment: str
    points: Mapping[str, ResultPoint] = field(default_factory=dict)


@dataclass(frozen=True)
class Dataset:
    """A complete, internally consistent set of benchmark results.

    Revision order is meaningful (it is the history axis) and is fixed by
    the loader — date-based, git-topology-based, or metadata-based
    depending on the input format.
    """

    project: str = ""
    revisions: tuple[Revision, ...] = ()
    environments: tuple[Environment, ...] = ()
    benchmarks: Mapping[str, Benchmark] = field(default_factory=dict)
    series: tuple[ResultSeries, ...] = ()

    def __post_init__(self):
        revision_ids = [r.id for r in self.revisions]
        for rid in revision_ids:
            if revision_ids.count(rid) > 1:
                raise ValueError(f"duplicate revision id {rid!r}")
        environment_ids = [e.id for e in self.environments]
        for eid in environment_ids:
            if environment_ids.count(eid) > 1:
                raise ValueError(f"duplicate environment id {eid!r}")
        for key, benchmark in self.benchmarks.items():
            if key != benchmark.name:
                raise ValueError(
                    f"benchmarks key {key!r} != benchmark name {benchmark.name!r}"
                )
        known_revisions = set(revision_ids)
        known_environments = set(environment_ids)
        seen_pairs: set[tuple[str, str]] = set()
        for series in self.series:
            pair = (series.benchmark, series.environment)
            if pair in seen_pairs:
                raise ValueError(
                    f"duplicate series for benchmark {series.benchmark!r} "
                    f"and environment {series.environment!r}"
                )
            seen_pairs.add(pair)
            if series.benchmark not in self.benchmarks:
                raise ValueError(
                    f"series references unknown benchmark {series.benchmark!r}"
                )
            if series.environment not in known_environments:
                raise ValueError(
                    f"series references unknown environment {series.environment!r}"
                )
            for rid in series.points:
                if rid not in known_revisions:
                    raise ValueError(
                        f"series {series.benchmark!r}/{series.environment!r} "
                        f"references unknown revision {rid!r}"
                    )

    @property
    def has_time_axis(self) -> bool:
        """False for a lone snapshot: with one revision there is no history
        to graph and generators render a table/bar view instead."""
        return len(self.revisions) > 1

    def revision_index(self, revision_id: str) -> int:
        """Position of a revision on the history axis."""
        for index, revision in enumerate(self.revisions):
            if revision.id == revision_id:
                return index
        raise KeyError(revision_id)

    def environment_axes(self) -> dict[str, tuple[str, ...]]:
        """Filter axes: each factor name mapped to its sorted distinct values."""
        values: dict[str, set[str]] = {}
        for environment in self.environments:
            for factor, value in environment.factors.items():
                values.setdefault(factor, set()).add(value)
        return {factor: tuple(sorted(vals)) for factor, vals in sorted(values.items())}

    def series_for(self, benchmark: str) -> tuple[ResultSeries, ...]:
        """All series (one per environment with results) for a benchmark."""
        return tuple(s for s in self.series if s.benchmark == benchmark)
