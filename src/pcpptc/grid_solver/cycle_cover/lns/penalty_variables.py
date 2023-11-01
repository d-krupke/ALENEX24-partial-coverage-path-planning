import math
import typing
from collections import defaultdict

import gurobipy as gp

from ...grid_instance import CoverageNecessity, PointBasedInstance, PointVertex
from ...grid_solution import FractionalSolution


class PenaltyVariables:
    """
    A dict that automatically creates all the penalty variables.
    """

    def __init__(
        self,
        instance: PointBasedInstance,
        area,
        fractional_solution: FractionalSolution,
        model: gp.Model,
    ):
        self._data = defaultdict(list)
        self.fractional_solution = fractional_solution
        for v in area:
            coverage_necessity = instance.coverage_necessities[v]
            if self._no_variables_necessary(coverage_necessity):
                continue
            min_cc = self._compute_cost_of_cheapest_cycle(instance, v)
            for p in coverage_necessity.penalty_vector:
                assert p > 0.0, "all penalties should be positive"
                if (
                    p < min_cc
                ):  # only if it is cheaper than the cheapest cycle_cover, it is useful to pay a penalty
                    x = model.addVar(vtype=gp.GRB.BINARY)
                    if fractional_solution.coverage(v) > 0:
                        x.start = 0
                    else:
                        x.start = 1
                    self._data[v].append((x, p))

    def _no_variables_necessary(self, coverage_necessity: CoverageNecessity) -> bool:
        if len(coverage_necessity) == 0:
            return True  # Doesn't need to be covered.
        if all(x == math.inf for x in coverage_necessity.penalty_vector):
            return True  # Not allowed to pay penalty instead
        return False

    def _compute_cost_of_cheapest_cycle(
        self, instance: PointBasedInstance, v: PointVertex
    ) -> float:
        n = min(
            instance.graph.neighbors(v),
            key=lambda n: instance.touring_costs.distance_cost_of_edge(v, n),
        )
        t0 = instance.touring_costs.turn_cost_at_vertex(v, (n, n))
        assert t0 >= 0
        t1 = instance.touring_costs.turn_cost_at_vertex(n, (v, v))
        assert t1 >= 0
        t1 = instance.touring_costs.turn_cost_at_vertex(n, (v, v))
        d = 2 * instance.touring_costs.distance_cost_of_edge(v, n)
        assert d >= 0
        return t0 + d + t1

    def obj(self):
        """
        Returns the penalty objective to be added to the LP objective.
        """
        if not self._data:
            return 0.0
        return sum(sum(x * p for (x, p) in l) for l in self._data.values())

    def __getitem__(self, item) -> typing.List[typing.Tuple[gp.Var, float]]:
        return self._data[item]
