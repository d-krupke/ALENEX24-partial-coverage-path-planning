import itertools
import math
import random
import typing

import networkx as nx

from ..grid_solver.grid_instance import (
    MultipliedTouringCosts,
    PointBasedInstance,
)
from ..polygon_instance import PolygonInstance
from ..utils.angles import turn_angle
from .graph import (
    attach_multiplier_to_graph,
    create_unit_graph,
    select_largest_component,
)
from .grid import SimpleSquareGrid
from .interface import PolygonToGridGraphCoveringConverter
from .polygonal_area import PolygonalArea

_POINT_BASED_DISTANCE = math.sqrt(2)
_EDGE_BASED_DISTANCE = 2


class RotatingRegularSquare(PolygonToGridGraphCoveringConverter):
    def identifier(self) -> str:
        return f"RotatingRegularSquare(fc={self.full_coverage}, pb={self.point_based})"

    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = point_based
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleSquareGrid(distance_factor=self._d)

    def _rate_graph(self, graph: nx.Graph) -> float:
        def vertex_cost(v):
            nbrs = list(graph.neighbors(v))
            if len(nbrs) < 2:
                return math.pi
            else:
                return min(
                    turn_angle(n[0], v, n[1]) for n in itertools.combinations(nbrs, 2)
                )

        return sum(vertex_cost(v) for v in graph.nodes)

    def _best_graph(self, pi: PolygonInstance) -> nx.Graph:
        best_graph = None
        best_value = None
        for i in range(0, 90, 3):
            grid_points = self.gridder(pi, angle=float(i))
            pe = PolygonalArea(polygon=pi.feasible_area)
            G = create_unit_graph(
                grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
            )
            G = select_largest_component(G)
            value = self._rate_graph(G)
            if best_value is None or best_value > value:
                best_graph = G
                best_value = value
        return best_graph

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        G = self._best_graph(pi)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 2

    def get_recommended_repetition_number(self) -> int:
        return 2


class RandomRegularSquare(PolygonToGridGraphCoveringConverter):
    def identifier(self) -> str:
        return f"RandomRegularSquare(fc={self.full_coverage}, pb={self.point_based})"

    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = point_based
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleSquareGrid(distance_factor=self._d)

    def _best_graph(self, pi: PolygonInstance, angle, translation) -> nx.Graph:
        grid_points = self.gridder(pi, angle=float(angle), translation=translation)
        pe = PolygonalArea(polygon=pi.feasible_area)
        G = create_unit_graph(
            grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
        )
        return select_largest_component(G)

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        angle = random.random() * math.pi
        tranlation = (
            random.random() * 2 * pi.tool_radius,
            random.random() * 2 * pi.tool_radius,
        )
        G = self._best_graph(pi, angle, tranlation)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 2

    def get_recommended_repetition_number(self) -> int:
        return 2


class RegularSquare(PolygonToGridGraphCoveringConverter):
    def identifier(self) -> str:
        return f"RegularSquare(fc={self.full_coverage}, pb={self.point_based})"

    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = False
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleSquareGrid(distance_factor=self._d)

    def _best_graph(self, pi: PolygonInstance, angle, translation) -> nx.Graph:
        grid_points = self.gridder(pi, angle=float(angle), translation=translation)
        pe = PolygonalArea(polygon=pi.feasible_area)
        G = create_unit_graph(
            grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
        )
        return select_largest_component(G)

    def __call__(
        self,
        pi: PolygonInstance,
        angle: float = 0.0,
        translation: typing.Tuple[float, float] = (0.0, 0.0),
    ) -> PointBasedInstance:
        G = self._best_graph(pi, angle, translation)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 2

    def get_recommended_repetition_number(self) -> int:
        return 2
