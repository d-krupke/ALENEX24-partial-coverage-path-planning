"""
Implements a set of methods to convert a polygonal instance to an instance on
a hexagonal grid.
Two important parameters:
* full_coverage: Every point in the grid will become necessary independent of the value
* point_based: A finer grid will be used that allows full coverage by simply visiting
                every point.


The three main algorithms are: Simple Grid (not rotated), Rotated Grid (based on cost
function), and Random Grid (simply a randomly orientated and translated hexagonal grid).
"""

import itertools
import math
import random

import networkx as nx

from ..grid_solver.grid_instance import (
    MultipliedTouringCosts,
    PointBasedInstance,
)
from ..polygon_instance import PolygonInstance
from ..utils import turn_angle
from .graph import (
    attach_multiplier_to_graph,
    create_delaunay_graph,
    select_largest_component,
)
from .grid import SimpleHexagonalGrid
from .grid.boundary import BoundaryGrid
from .grid.density_filter import DensityFilter
from .interface import PolygonToGridGraphCoveringConverter
from .polygonal_area import PolygonalArea

_POINT_BASED_DISTANCE = 3 / math.sqrt(3)
_EDGE_BASED_DISTANCE = 4 / math.sqrt(3)


class RegularHexagonal(PolygonToGridGraphCoveringConverter):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = False
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleHexagonalGrid(distance_factor=self._d)

    def __call__(self, pi: PolygonInstance, angle: float = 0.0) -> PointBasedInstance:
        grid_points = self.gridder(pi, angle=angle)
        pe = PolygonalArea(polygon=pi.feasible_area)
        G = create_delaunay_graph(
            grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
        )
        G = select_largest_component(G)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return (
            f"RegularHexagonal(full_coverage={self.full_coverage},"
            f" point_based={self.point_based})"
        )


class RotatingRegularHexagonal(PolygonToGridGraphCoveringConverter):
    """
    Rotates a hexagonal grid such that the sum of expected turn costs for each point is
    minimal. The cost for a point is considered the minimal cost of covering
    it within the grid (actually a variant of delaunay is used).
    """

    def __init__(
        self, full_coverage=False, point_based=False, with_boundary: bool = False
    ):
        super().__init__(full_coverage=full_coverage)
        self.point_based = point_based
        self.with_boundary = with_boundary
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleHexagonalGrid(distance_factor=self._d)

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
        if self.with_boundary:
            boundary_grid = list(
                BoundaryGrid(
                    reduction_factor=0.05, distance_factor=self._d * pi.tool_radius
                )(pi)
            )
            print(f"{len(boundary_grid)} points on the boundary")
        else:
            boundary_grid = None
        for i in range(0, 60, 2):
            grid_points = self.gridder(pi, angle=float(i))
            if self.with_boundary:
                grid_points += boundary_grid
            pe = PolygonalArea(polygon=pi.feasible_area)
            G = create_delaunay_graph(
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
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return (
            f"RotatingRegularHexagonal(full_coverage={self.full_coverage},"
            f" point_based={self.point_based}, with_boundary={self.with_boundary})"
        )


class RotatingHexagonalWithBoundary(PolygonToGridGraphCoveringConverter):
    def identifier(self) -> str:
        return (
            f"RotatingHexagonalWithBoundary(full_coverage={self.full_coverage},"
            f" point_based={self.point_based})"
        )

    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = False
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleHexagonalGrid(distance_factor=self._d)

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
        for i in range(0, 60, 2):
            grid_points = self.gridder(pi, angle=float(i))
            grid_points += list(BoundaryGrid()(pi))
            df = DensityFilter(
                min_distance=0.25 * pi.tool_radius,
                max_neighbors=8,
                radius=1.1 * self._d * pi.tool_radius,
            )
            grid_points = list(df(grid_points))
            pe = PolygonalArea(polygon=pi.feasible_area)
            G = create_delaunay_graph(
                grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
            )
            G = select_largest_component(G)
            value = self._rate_graph(G)
            if best_value is None or best_value > value:
                best_graph = G
                best_value = value
            print("Rotating hexgonal grid:", i, value)
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
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2


class RandomRegularHexagonal(PolygonToGridGraphCoveringConverter):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = point_based
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleHexagonalGrid(distance_factor=self._d)

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        angle = random.random() * math.pi
        tranlation = (
            random.random() * 2 * pi.tool_radius,
            random.random() * 2 * pi.tool_radius,
        )
        grid_points = self.gridder(pi, angle=angle, translation=tranlation)
        pe = PolygonalArea(polygon=pi.feasible_area)
        G = create_delaunay_graph(
            grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
        )
        G = select_largest_component(G)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return (
            f"RandomRegularHexagonal(full_coverage={self.full_coverage},"
            f" point_based={self.point_based})"
        )


class RandomRegularHexagonalWithBoundary(PolygonToGridGraphCoveringConverter):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(full_coverage=full_coverage)
        self.point_based = False
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE
        self.gridder = SimpleHexagonalGrid(distance_factor=self._d)

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        angle = random.random() * math.pi
        tranlation = (
            random.random() * 2 * pi.tool_radius,
            random.random() * 2 * pi.tool_radius,
        )
        grid_points = self.gridder(pi, angle=angle, translation=tranlation)
        grid_points += list(BoundaryGrid()(pi))
        df = DensityFilter(
            min_distance=pi.tool_radius,
            max_neighbors=8,
            radius=1.1 * self._d * pi.tool_radius,
        )
        grid_points = list(df(grid_points))
        pe = PolygonalArea(polygon=pi.feasible_area)
        G = create_delaunay_graph(
            grid_points, length_limit=1.1 * self._d * pi.tool_radius, polygon=pe
        )
        G = select_largest_component(G)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return (
            f"RandomRegularHexagonalWithBoundary(full_coverage={self.full_coverage},"
            f" point_based={self.point_based})"
        )
