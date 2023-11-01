import unittest

import networkx as nx
from cycle_cover.fractional_grid_solver.solver import FractionalGridSolver
from grid_instance.coverage_necessity import (
    MultiCoverage,
    OptionalCoverage,
    SimpleCoverage,
)
from grid_instance.vertex_passage import VertexPassage
from optimizer.utils import (
    CoverageNecessities,
    FractionalSolution,
    PointBasedInstance,
    PointVertex,
    TouringCosts,
)

P = PointVertex


class TestSolver(unittest.TestCase):
    def test_trivial(self):
        p0 = P(0.0, 0.0)
        p1 = P(1.0, 1.0)
        p2 = P(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = TouringCosts(1.0, 1.0)
        instance = PointBasedInstance(G, obj, CoverageNecessities(SimpleCoverage()))
        sol = FractionalGridSolver()(instance)
        sol_opt = FractionalSolution()
        sol_opt[VertexPassage(v=p0, end_a=p1, end_b=p2)] = 1.0
        sol_opt[VertexPassage(v=p1, end_a=p0, end_b=p2)] = 1.0
        sol_opt[VertexPassage(v=p2, end_a=p1, end_b=p0)] = 1.0
        assert sol == sol_opt

    def test_trivial_all_free(self):
        p0 = P(0.0, 0.0)
        p1 = P(1.0, 1.0)
        p2 = P(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = TouringCosts(1.0, 1.0)
        coverage_necessities = CoverageNecessities(SimpleCoverage())
        coverage_necessities[p0] = OptionalCoverage()
        coverage_necessities[p1] = OptionalCoverage()
        coverage_necessities[p2] = OptionalCoverage()
        instance = PointBasedInstance(G, obj, coverage_necessities)
        sol = FractionalGridSolver()(instance)
        sol_opt = FractionalSolution()
        assert sol == sol_opt

    def test_double_coverage(self):
        for k in range(1, 5):
            p00 = PointVertex(0.0, 0.0)
            p11 = PointVertex(1.0, 1.0)
            p10 = PointVertex(1.0, 0.0)
            p01 = PointVertex(0.0, 1.0)
            G = nx.Graph()
            G.add_nodes_from([p00, p10, p01, p11])
            G.add_edges_from([(p00, p01), (p00, p10), (p10, p11), (p01, p11)])
            obj = TouringCosts(1.0, 1.0)
            coverage_necessities = CoverageNecessities(SimpleCoverage())
            coverage_necessities[p00] = MultiCoverage(k)
            instance = PointBasedInstance(G, obj, coverage_necessities)
            sol = FractionalGridSolver()(instance)
            self.assertAlmostEqual(sum(v for k, v in sol.at_vertex(p00).items()), k, 2)

    def test_trivial_all_but_one_free(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = TouringCosts(distance_cost=0.0, turn_cost=1.0)
        coverage_necesseties = CoverageNecessities(SimpleCoverage())
        coverage_necesseties[p0] = OptionalCoverage()
        coverage_necesseties[p1] = OptionalCoverage()
        instance = PointBasedInstance(G, obj, coverage_necesseties)
        sol = FractionalGridSolver()(instance)
        for k, v in sol:
            print(k, v)
        sol_opt = FractionalSolution()
        sol_opt[VertexPassage(v=p0, end_a=p2, end_b=p2)] = 0.5
        sol_opt[VertexPassage(v=p1, end_a=p2, end_b=p2)] = 0.5
        sol_opt[VertexPassage(v=p2, end_a=p1, end_b=p0)] = 1.0
        assert sol == sol_opt

    def test_large_grid(self):
        points = {}
        for x in range(0, 100):
            for y in range(0, 100):
                points[(x, y)] = P(x, y)
        G = nx.Graph()
        G.add_nodes_from(points.values())
        for x in range(0, 100):
            for y in range(0, 100):
                if x > 0:
                    G.add_edge(points[(x, y)], points[(x - 1, y)])
                if y > 0:
                    G.add_edge(points[(x, y)], points[(x, y - 1)])
                if x > 0 and y > 0:
                    G.add_edge(points[(x, y)], points[(x - 1, y - 1)])
        obj = TouringCosts(distance_cost=0.1, turn_cost=1.0)
        instance = PointBasedInstance(G, obj, CoverageNecessities(SimpleCoverage()))
        sol = FractionalGridSolver()(instance)
