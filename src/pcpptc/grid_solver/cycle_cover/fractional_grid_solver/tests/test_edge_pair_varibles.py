import unittest

import gurobipy as gp
import networkx as nx
from cycle_cover.fractional_grid_solver.vertex_passage_variables import (
    VertexPassageVariablesInGraph,
)
from grid.grid_point import GridPoint
from optimizer.utils import CoverageNecessities, PointBasedInstance, TouringCosts


class TestEdgePairVariables(unittest.TestCase):
    def _build_simple_graph(self):
        G = nx.Graph()
        points = [
            GridPoint(0, 0),
            GridPoint(1.0, 0.0),
            GridPoint(1.0, 1.0),
            GridPoint(0.0, 1.0),
        ]
        G.add_nodes_from(points)
        G.add_edge(points[0], points[1])
        G.add_edge(points[1], points[2])
        G.add_edge(points[2], points[3])
        G.add_edge(points[3], points[0])
        G.add_edge(points[0], points[2])
        return G, points

    def test_number_of_coverage_variables(self):
        model = gp.Model("test")
        G, points = self._build_simple_graph()
        instance = PointBasedInstance(G, TouringCosts(1.0, 1.0), CoverageNecessities())
        epv = VertexPassageVariablesInGraph(instance, model)
        for v in G.nodes():
            d = G.degree(v)
            u_turns = d
            normal_turns = d * (d - 1) / 2
            assert u_turns + normal_turns == len([vp for vp in epv if vp.v == v])

    def test_number_of_variables(self):
        model = gp.Model("test")
        G, points = self._build_simple_graph()
        instance = PointBasedInstance(G, TouringCosts(1.0, 1.0), CoverageNecessities())
        epv = VertexPassageVariablesInGraph(instance, model=model)
        assert 8 + G.number_of_edges() * 2 == len(epv)

    def test_number_of_edge_coverage_variables(self):
        model = gp.Model("test")
        G, points = self._build_simple_graph()
        instance = PointBasedInstance(G, TouringCosts(1.0, 1.0), CoverageNecessities())
        epv = VertexPassageVariablesInGraph(instance=instance, model=model)
        print([vp for vp in epv if vp.v == points[0]])
        assert len([vp for vp in epv if vp.v == points[1]]) == 3
        assert 3 + 3 == len([vp for vp in epv if vp.v == points[0]])
