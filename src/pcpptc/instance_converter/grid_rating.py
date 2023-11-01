import itertools
import math

import networkx as nx

from ..grid_solver.grid_instance import PointVertex
from ..polygon_instance import PolygonInstance
from ..utils import turn_angle


class GridRating:
    def __init__(self, pi: PolygonInstance):
        self.instance = pi

    def _coverage_value(self, graph: nx.Graph) -> float:
        return graph.number_of_nodes()

    def _vertex_cost(self, graph: nx.Graph, v: PointVertex):
        nbrs = list(graph.neighbors(v))
        if len(nbrs) < 2:
            return math.pi
        else:
            return min(
                turn_angle(n[0], v, n[1]) for n in itertools.combinations(nbrs, 2)
            )

    def _cost(self, graph: nx.Graph) -> float:
        return sum(self._vertex_cost(graph, v) for v in graph.nodes)

    def __call__(self, graph: nx.Graph) -> float:
        return self._coverage_value(graph) / self._cost(graph)
