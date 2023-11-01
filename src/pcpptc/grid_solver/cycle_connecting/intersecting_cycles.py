import typing
from collections import defaultdict

from ..grid_instance import PointBasedInstance, VertexPassage
from ..grid_solution import FractionalSolution


class IntersectingVertexPassageConnection:
    """
    Finds the cheapest direct connection of intersecting cycles.
    """

    def __init__(self, instance: PointBasedInstance):
        self._instance = instance
        self._sources = defaultdict(list)

    def add_source(self, source: VertexPassage):
        if source not in self._sources[source.v]:
            self._sources[source.v].append(source)

    def _replacements(
        self, source: VertexPassage, target: VertexPassage
    ) -> typing.Tuple[VertexPassage, VertexPassage]:
        assert target.v == source.v
        a0 = VertexPassage(end_a=source.end_a, v=source.v, end_b=target.end_a)
        a1 = VertexPassage(end_a=source.end_b, v=source.v, end_b=target.end_b)
        b0 = VertexPassage(end_a=source.end_a, v=source.v, end_b=target.end_b)
        b1 = VertexPassage(end_a=source.end_b, v=source.v, end_b=target.end_a)
        if self._c(a0) + self._c(a1) < self._c(b0) + self._c(b1):
            return a0, a1
        else:
            return b0, b1

    def _c(self, vp: VertexPassage) -> float:
        return self._instance.touring_costs.turn_cost_at_vertex(
            at=vp.v, ends=vp.endpoints()
        )

    def _get_best_source(
        self, target: VertexPassage
    ) -> typing.Tuple[VertexPassage, float]:
        candidates = self._sources[target.v]

        def obj(source: VertexPassage) -> float:
            return sum(self._c(vp) for vp in self._replacements(source, target)) - (
                self._c(target) + self._c(source)
            )

        best_source = min(candidates, key=obj)
        return best_source, obj(best_source)

    def get_cost(self, target: VertexPassage) -> float:
        if not self._sources[target.v]:
            return float("inf")
        return self._get_best_source(target)[1]

    def get_connection(
        self, target: VertexPassage
    ) -> typing.Tuple[FractionalSolution, VertexPassage]:
        source, cost = self._get_best_source(target)
        assert source.v == target.v
        fs = FractionalSolution()
        fs.add(target, -1.0)
        fs.add(source, -1.0)
        for vp in self._replacements(source, target):
            fs.add(vp, 1.0)
        return fs, source
