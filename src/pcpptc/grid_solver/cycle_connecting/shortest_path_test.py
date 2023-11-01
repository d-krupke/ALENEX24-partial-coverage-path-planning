import math
import unittest

import networkx as nx

from ..grid_instance import (
    CoverageNecessities,
    OptionalCoverage,
    PointBasedInstance,
    PointVertex,
    SimpleTouringCosts,
    VertexPassage,
)
from ..grid_solution import (
    FractionalSolution,
    create_cycle_solution,
    is_feasible_cycle_cover,
)
from .dedge_dijkstra import DEdgeDijkstraTree
from .shortest_path import CycleCheapestConnection


class DijkstraTest(unittest.TestCase):
    def test_2x5(self):
        points = [[PointVertex(x, y) for x in range(5)] for y in range(2)]
        graph = nx.Graph()
        for row in points:
            for point in row:
                graph.add_node(point)
        for x in range(4):
            for y in range(2):
                graph.add_edge(points[y][x], points[y][x + 1])
        for x in range(5):
            graph.add_edge(points[0][x], points[1][x])
        instance = PointBasedInstance(
            graph,
            SimpleTouringCosts(distance_factor=1, turn_factor=5),
            CoverageNecessities(OptionalCoverage()),
        )
        fs = FractionalSolution()
        fs[VertexPassage(points[0][0], points[1][0], points[0][1])] = 1.0
        fs[VertexPassage(points[1][0], points[0][0], points[1][1])] = 1.0
        fs[VertexPassage(points[1][1], points[1][0], points[0][1])] = 1.0
        fs[VertexPassage(points[0][1], points[0][0], points[1][1])] = 1.0

        fs[VertexPassage(points[0][3], points[1][3], points[0][4])] = 1.0
        fs[VertexPassage(points[1][3], points[0][3], points[1][4])] = 1.0
        fs[VertexPassage(points[1][4], points[1][3], points[0][4])] = 1.0
        fs[VertexPassage(points[0][4], points[0][3], points[1][4])] = 1.0

        assert is_feasible_cycle_cover(instance, fs)
        self.assertAlmostEqual(fs.angle_sum(), 4 * math.pi, 3)

        cc = create_cycle_solution(instance.graph, fs)
        assert len(cc) == 2

        assert cc[0].length() == 4.0
        self.assertAlmostEqual(cc[0].angle_sum(), 2 * math.pi, 3)
        self.assertAlmostEqual(cc[1].angle_sum(), 2 * math.pi, 3)

        c = cc[0] if points[0][0] in cc[0].covered_vertices() else cc[1]

        # dijkstra = DijkstraTree(polygon, c)
        # self.assertEqual(dijkstra.get_path((waypoints[1][2], waypoints[1][3])),
        #                 [(waypoints[1][1], waypoints[1][2]), (waypoints[1][2], waypoints[1][3])])
        #
        #        self.assertEqual(dijkstra.get_path((waypoints[1][3], waypoints[0][3])),
        #                         [(waypoints[1][1], waypoints[1][2]), (waypoints[1][2], waypoints[1][3]),
        #                          (waypoints[1][3], waypoints[0][3])])

        vp = VertexPassage(points[0][3], points[1][3], points[0][4])
        # self.assertAlmostEqual(
        #    dijkstra._passage_cost(vp, waypoints[0][2], include_distance=False), 0, 2)
        # self.assertAlmostEqual(dijkstra.estimate_cost_of_passage(vp), 4, 3)

        dd = DEdgeDijkstraTree(instance)
        dd.update((points[1][1], points[1][2]), 0.0)
        dd.propagate()
        self.assertAlmostEqual(dd.cost((points[1][2], points[1][3])), 1.0, 2)
        ccc = CycleCheapestConnection(instance, c)
        self.assertAlmostEqual(ccc.get_cost(cc[0] if c == cc[1] else cc[1]), 4.0, 2)
