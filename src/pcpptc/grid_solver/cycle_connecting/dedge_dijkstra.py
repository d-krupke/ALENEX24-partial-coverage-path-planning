import math
import typing
import unittest
from collections import deque

import networkx as nx

from ..grid_instance import PointBasedInstance, PointVertex, SimpleTouringCosts

DEdge = typing.Tuple[PointVertex, PointVertex]


class EdgeCostFunction:
    """
    Cost function
    """

    def __init__(self, instance: PointBasedInstance, multiplier: float = 1.0):
        self._instance = instance
        self._multiplier = multiplier

    def __call__(self, e: DEdge, predecessor: DEdge) -> float:
        assert predecessor[1] == e[0], "Should be connected"
        d = self._instance.touring_costs.distance_cost_of_edge(e[0], e[1])
        t = self._instance.touring_costs.turn_cost_at_vertex(
            at=e[0], ends=(predecessor[0], e[1])
        )
        return self._multiplier * (d + t)


class DEdgeDijkstraTree:
    """
    The paths point from source to target. Check the asserts in `get_path`.
    """

    def __init__(
        self,
        instance: PointBasedInstance,
        epsilon: float = 1e-4,
        cost_function: typing.Optional[EdgeCostFunction] = None,
    ):
        self._instance = instance
        self._improved_edges = deque()
        self._predecessors = {}
        self._costs = {}
        self._epsilon = epsilon
        if cost_function:
            self._cost_function = cost_function
        else:
            self._cost_function = EdgeCostFunction(instance)

    def propagate(self):
        """
        Propagates the updated costs through the shortest path tree. If there are no
        updates necessary, the call is cheap.
        """
        while self._improved_edges:
            e = self._improved_edges.popleft()
            cost_to_e = self._costs[e]
            for successor_vertices in self._instance.graph.neighbors(e[1]):
                successor_edge = (e[1], successor_vertices)
                cost = cost_to_e + self._cost_function(successor_edge, predecessor=e)
                self.update(successor_edge, cost, predecessor=e)

    def update(
        self, e: DEdge, value: float, predecessor: typing.Optional[DEdge] = None
    ) -> bool:
        """
        Updates the cost of reaching an edge. Used for initialization of the source
        as well as for propagating updates.
        There is an epsilon to prevent tiny changes to propagate through the whole graph
        due to floating point imprecision.
        """
        if self._costs.get(e, float("inf")) - self._epsilon > value:
            self._costs[e] = value
            self._improved_edges.append(e)
            self._predecessors[e] = predecessor
            return True
        else:
            return False

    def cost(self, e: DEdge) -> float:
        """
        Returns the cost to this edge.
        """
        return self._costs.get(e, float("inf"))

    def get_path(self, target: DEdge) -> typing.List[DEdge]:
        path = [target]
        e = self._predecessors[target]
        while e:
            path.append(e)
            e = self._predecessors[e]
        path = path[::-1]
        assert path[-1] == target
        assert all(path[i][1] == path[i + 1][0] for i in range(len(path) - 1))
        return path


class DEdgeDijkstraTreeTest(unittest.TestCase):
    def test_no_turn_line_no_cost(self):
        length = 10
        points = [PointVertex(i, 0.0) for i in range(length)]
        G = nx.Graph()
        G.add_nodes_from(points)
        for i in range(length - 1):
            G.add_edge(points[i], points[i + 1])
        instance = PointBasedInstance(
            G, SimpleTouringCosts(turn_factor=0.0, distance_factor=0.0), None
        )
        dtree = DEdgeDijkstraTree(instance)
        dtree.update((points[0], points[1]), 0.0)
        dtree.propagate()
        assert dtree.cost((points[-2], points[-1])) == 0.0

    def test_no_turn_double_line(self):
        length = 10
        points = [PointVertex(i, 0.0) for i in range(length)]
        points_double = [PointVertex(i, 1.0) for i in range(length)]
        G = nx.Graph()
        G.add_nodes_from(points)
        for i in range(length - 1):
            G.add_edge(points[i], points[i + 1])
            G.add_edge(points_double[i], points_double[i + 1])
        for i in range(length):
            G.add_edge(points[i], points_double[i])
        instance = PointBasedInstance(
            G, SimpleTouringCosts(turn_factor=5.0, distance_factor=1.0), None
        )
        dtree = DEdgeDijkstraTree(instance)
        dtree.update((points[0], points[1]), 0.0)
        dtree.propagate()
        assert dtree.cost((points[-2], points[-1])) == length - 2
        path = dtree.get_path((points[-2], points[-1]))
        for i in range(length - 1):
            assert path[i][0] == points[i]

    def test_no_turn_line(self):
        length = 10
        points = [PointVertex(i, 0.0) for i in range(length)]
        G = nx.Graph()
        G.add_nodes_from(points)
        for i in range(length - 1):
            G.add_edge(points[i], points[i + 1])
        instance = PointBasedInstance(
            G, SimpleTouringCosts(turn_factor=5.0, distance_factor=1.0), None
        )
        dtree = DEdgeDijkstraTree(instance)
        dtree.update((points[0], points[1]), 0.0)
        dtree.propagate()
        assert dtree.cost((points[-2], points[-1])) == length - 2

    def test_l_line_no_turncost(self):
        length = 10
        turn_at = 5
        points = [
            PointVertex(i, 0.0) if i < turn_at else PointVertex(turn_at, i - turn_at)
            for i in range(length)
        ]
        G = nx.Graph()
        G.add_nodes_from(points)
        for i in range(length - 1):
            G.add_edge(points[i], points[i + 1])
        instance = PointBasedInstance(
            G, SimpleTouringCosts(turn_factor=0.0, distance_factor=1.0), None
        )
        dtree = DEdgeDijkstraTree(instance)
        dtree.update((points[0], points[1]), 0.0)
        dtree.propagate()
        assert dtree.cost((points[-2], points[-1])) == length - 2

    def test_l_line(self):
        length = 10
        for turn_at in range(1, length - 1):
            points = [
                PointVertex(i, 0.0)
                if i < turn_at
                else PointVertex(turn_at, i - turn_at)
                for i in range(length)
            ]
            G = nx.Graph()
            G.add_nodes_from(points)
            for i in range(length - 1):
                G.add_edge(points[i], points[i + 1])
            instance = PointBasedInstance(
                G, SimpleTouringCosts(turn_factor=5.0, distance_factor=1.0), None
            )
            dtree = DEdgeDijkstraTree(instance)
            dtree.update((points[0], points[1]), 0.0)
            dtree.propagate()
            assert dtree.cost((points[-2], points[-1])) == length - 2 + 5 * 0.5 * math.pi
