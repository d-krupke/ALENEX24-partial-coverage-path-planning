import math
import typing

from pcpptc.utils import abs_angle_difference, direction, turn_angle

from ...grid_instance import PointBasedInstance, PointVertex
from ...grid_solution import FractionalSolution


class OrientationListObjective:
    """
    Rates a list of orientations. No consideration of the dominance of orientations.
    """

    def __init__(
        self,
        instance: PointBasedInstance,
        fractional_solution: FractionalSolution,
        neighbor_factor: float = 0.1,
        passage_factor: float = 1.0,
    ):
        self.instance = instance
        self.fractional_solution = fractional_solution
        self.neighbor_factor = neighbor_factor
        self.passage_factor = passage_factor

    def neighbor_direction_difference(
        self, v: PointVertex, orientations: typing.List[float]
    ) -> float:
        """
        The sum of difference to the neighbors in the graph. Is independent of the
        solution.
        """
        sum_cost = 0.0
        for n in self.instance.graph.neighbors(v):
            d = direction(n.point, origin=v.point)
            c = min(
                min(abs_angle_difference(o, d), abs_angle_difference(o + math.pi, d))
                for o in orientations
            )
            sum_cost += c
        return sum_cost

    def passing_cost_difference(
        self, v: PointVertex, orientations: typing.List[float]
    ) -> float:
        vertex_passages = self.fractional_solution.at_vertex(v)
        return sum(
            x
            * min(
                abs(
                    turn_angle(vp.end_a, vp.v, vp.end_b, forced_orientation_at_v1=o)
                    - turn_angle(vp.end_a, vp.v, vp.end_b)
                )
                for o in orientations
            )
            for vp, x in vertex_passages.items()
        )
        """

        def cost_diff(vp, o):
            tc = self.polygon.touring_costs.turn_cost_at_vertex
            forced = tc(at=vp.v, ends=vp.endpoints(), forced_orientation=o)
            normal = tc(at=vp.v, ends=vp.endpoints(), forced_orientation=o)
            assert forced >= normal
            return forced - normal

        return sum(x * min(cost_diff(vp, o) for o in orientations) for vp, x in
                   vertex_passages.items())
        """
        return None

    def __call__(self, v: PointVertex, orientations: typing.List[float]) -> float:
        n = self.neighbor_factor * self.neighbor_direction_difference(v, orientations)
        p = self.passage_factor * self.passing_cost_difference(v, orientations)
        return n + p
