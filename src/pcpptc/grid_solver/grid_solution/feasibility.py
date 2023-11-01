import typing
import unittest

import networkx as nx

from ..grid_instance.coverage_necessity import (
    CoverageNecessities,
    SimpleCoverage,
)
from ..grid_instance.grid_instance import PointBasedInstance
from ..grid_instance.muliplied_touring_costs import (
    SimpleTouringCosts,
)
from ..grid_instance.point import PointVertex
from ..grid_instance.vertex_passage import VertexPassage
from .create_minimal_instance import create_minimal_graph_from_solution
from .fractional_solution import FractionalSolution


def _calculate_flow_at(
    v: PointVertex, out: PointVertex, graph: nx.Graph, solution: FractionalSolution
) -> float:
    v_sum = 0.0
    for n in graph.neighbors(v):
        vp = VertexPassage(v, end_a=out, end_b=n)
        if n != out:
            v_sum += solution[vp]
        else:
            v_sum += 2 * solution[vp]  # u-turn that uses this passage twice
    return v_sum


def are_all_passages_between_neighbors(graph: nx.Graph, solution: FractionalSolution):
    for vp, _x in solution:
        for n in vp.endpoints():
            if (vp.v, n) not in graph.edges and (n, vp.v) not in graph.edges:
                return False
    return True


class NotFlowFeasible(Exception):
    def __init__(self, v, w, diff):
        self.v = v
        self.w = w
        self.diff = diff

    def __str__(self):
        return f"NotFlowFeasible({self.v}, {self.w}, {self.diff})"


def is_flow_feasible(
    solution: FractionalSolution,
    instance: typing.Optional[PointBasedInstance] = None,
    eps=1e-5,
    raise_exception: bool = False,
):
    """
    Checks if every edge has the same amount of incoming and outgoing passages.
    """
    graph = instance.graph if instance else create_minimal_graph_from_solution(solution)
    for v, w in graph.edges:
        diff = abs(
            _calculate_flow_at(v, w, graph, solution)
            - _calculate_flow_at(w, v, graph, solution)
        )
        if diff > eps:
            if raise_exception:
                raise NotFlowFeasible(v, w, diff)
            return False
    return True


class InsufficientCoverage(Exception):
    def __init__(
        self, instance: PointBasedInstance, fs: FractionalSolution, vertex: PointVertex
    ):
        self.instance = instance
        self.solution = fs
        self.vertex = vertex


def is_covered(
    instance: PointBasedInstance, solution: FractionalSolution, raise_exception=False
):
    """
    Checks if all necessary parts of the polygon are covered sufficiently.
    """
    for v in instance.graph.nodes:
        cn = instance.coverage_necessities[v]
        coverage = sum(x for x in solution.at_vertex(v).values())
        if coverage < cn.number_of_necessary_coverages():
            if raise_exception:
                raise InsufficientCoverage(instance, solution, v)
            return False
    return True


def is_integral(solution: FractionalSolution, eps=1e-5):
    """
    Checks if the fractional solution is integral.
    """
    return all(abs(x - round(x)) <= eps for vp, x in solution)


def is_feasible_cycle_cover(
    instance: PointBasedInstance, solution: FractionalSolution, verbose: bool = False
):
    """
    Checks if an polygon is a feasible, integral cycle_cover cover.
    """
    if verbose:
        if not is_integral(solution):
            print("Solution not integral")
            return False
        if not is_flow_feasible(solution):
            print("Solution is not flow-feasible")
            return False
        if not is_covered(instance, solution):
            print("Solution does not cover all necessary waypoints")
            return False
        if not are_all_passages_between_neighbors(instance.graph, solution):
            print("Solution uses illegal passages.")
            return False
        return True
    return (
        is_integral(solution)
        and is_flow_feasible(solution)
        and is_covered(instance, solution)
        and are_all_passages_between_neighbors(instance.graph, solution)
    )


class TestFeasibility(unittest.TestCase):
    def test_fractional(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = SimpleTouringCosts(1.0, 1.0)
        instance = PointBasedInstance(G, obj, CoverageNecessities(SimpleCoverage()))
        solution = FractionalSolution()
        solution[VertexPassage(p0, p1, p2)] = 0.5
        solution[VertexPassage(p1, p0, p2)] = 0.5
        solution[VertexPassage(p2, p1, p0)] = 0.5
        assert not is_feasible_cycle_cover(instance, solution)

    def test_feasible(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = SimpleTouringCosts(1.0, 1.0)
        instance = PointBasedInstance(G, obj, CoverageNecessities(SimpleCoverage()))
        solution = FractionalSolution()
        solution[VertexPassage(p0, p1, p2)] = 1.0
        solution[VertexPassage(p1, p0, p2)] = 1.0
        solution[VertexPassage(p2, p1, p0)] = 1.0
        assert is_feasible_cycle_cover(instance, solution)

    def test_flow(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = SimpleTouringCosts(1.0, 1.0)
        solution = FractionalSolution()
        solution[VertexPassage(p0, p1, p1)] = 1.0
        solution[VertexPassage(p1, p0, p2)] = 1.0
        solution[VertexPassage(p2, p1, p0)] = 1.0
        assert not is_flow_feasible(solution)

    def test_covered(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        G = nx.Graph()
        G.add_nodes_from([p0, p1, p2])
        G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
        obj = SimpleTouringCosts(1.0, 1.0)
        instance = PointBasedInstance(G, obj, CoverageNecessities(SimpleCoverage()))
        solution = FractionalSolution()
        solution[VertexPassage(p0, p1, p1)] = 1.0
        solution[VertexPassage(p1, p0, p0)] = 1.0
        assert not is_covered(instance, solution)
