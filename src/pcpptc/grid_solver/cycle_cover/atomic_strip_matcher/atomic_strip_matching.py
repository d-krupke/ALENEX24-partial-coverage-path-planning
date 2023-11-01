import unittest

import networkx as nx
from blossomv import blossomv

from ...grid_instance import PointVertex, SimpleTouringCosts, VertexPassage
from ...grid_solution import FractionalSolution
from .atomic_strip import AtomicStrip, AtomicStrips
from .atomic_strip_edges import AtomicStripEdges
from .atomic_strip_vertex import AtomicStripVertex
from .transition_cost import TransitionCostCalculator


class AtomicStripMatching:
    def __init__(self, graph: nx.Graph, transition_costs: TransitionCostCalculator):
        self.atomic_strips = AtomicStrips()
        self.edges = AtomicStripEdges()
        self.graph = graph
        self.transition_costs = transition_costs
        self._matching_partner = {}

    def _add_skip_edge(self, atomic_strip: AtomicStrip, weight: float):
        self.edges.create(atomic_strip.vertices[0], atomic_strip.vertices[1], weight)

    def connect_strips_fully(self, s0: AtomicStrip, s1: AtomicStrip):
        for v0 in s0.vertices:
            for v1 in s1.vertices:
                weight = self.transition_costs(v0, v1)
                if not abs(self.transition_costs(v1, v0) - weight) <= max(
                    0.001 * weight, 0.001
                ):
                    print(weight)
                    print(self.transition_costs(v1, v0))
                assert abs(self.transition_costs(v1, v0) - weight) <= max(
                    0.001 * weight, 0.001
                ), "Should be equal"
                self.edges.create(v0, v1, weight)

    def add_edge(
        self, v0: AtomicStripVertex, v1: AtomicStripVertex, weight: float
    ) -> bool:
        """
        If the edge already exists, the weight is adapted to the minimum weight.
        """
        exists = self.edges.contains_edge_between(v0, v1)
        if weight < 0:
            msg = "Only values >=0.0 are allowed."
            raise ValueError(msg)
        if exists:
            e = self.edges.get_edge_between(v0, v1)
            e.weight = min(e.weight, weight)
            return True
        else:
            self.edges.create(v0, v1, weight)
            return False

    def _connect_to_all_neighbored_strips(self, s: AtomicStrip):
        point = s.point_vertex
        for n in self.graph.neighbors(point):
            for s2 in self.atomic_strips.get_atomic_strips_of_point(n):
                self.connect_strips_fully(s, s2)

    def create_atomic_strip(self, point: PointVertex, orientation: float):
        s = self.atomic_strips.create(point, orientation)
        self._connect_to_all_neighbored_strips(s)
        return s

    def add_skip_penalty(self, atomic_strip: AtomicStrip, skip_penalty: float):
        assert skip_penalty >= 0, "Non-negative skip penalties are prohibited."
        self._add_skip_edge(atomic_strip, skip_penalty)

    def solve(self):
        edges = {
            (e.vertices[0].index, e.vertices[1].index): e.weight for e in self.edges
        }
        print(f"Solve matching on {len(self.edges)} edges.")
        matching = blossomv.min_weight_perfect_matching(edges)
        self._matching_partner = {
            self.atomic_strips.vertices[e[0]]: self.atomic_strips.vertices[e[1]]
            for e in matching
        }
        self._matching_partner.update(
            {
                self.atomic_strips.vertices[e[1]]: self.atomic_strips.vertices[e[0]]
                for e in matching
            }
        )
        return [
            (self.atomic_strips.vertices[e[0]], self.atomic_strips.vertices[e[1]])
            for e in matching
        ]

    def __getitem__(self, item):
        return self._matching_partner[item]

    def walk(self, v):
        """
        Walks through a cycle_cover of matched atomic strip vertices.
        Can only be called after `solve()`!
        """
        start = v
        yield v
        v = self[v]
        yield v
        v = self.atomic_strips.vertices.get_partner(v)
        while v != start:
            yield v
            v = self[v]
            if v == start:
                break
            yield v
            v = self.atomic_strips.vertices.get_partner(v)

    def to_solution(self) -> FractionalSolution:
        fractional_solution = FractionalSolution()
        already_visited_vertices = set()
        for v in self.atomic_strips.vertices:
            if v not in already_visited_vertices:
                c = list(self.walk(v))
                if len(c) > 2:
                    points = []
                    for v_ in c:
                        already_visited_vertices.add(v_)
                        if not points or v_.point_vertex != points[-1]:
                            points.append(v_.point_vertex)
                    if points[-1] == points[0]:
                        points.pop()
                    for i in range(len(points)):
                        j = (i + 1) % len(points)
                        k = (i + 2) % len(points)
                        vp = VertexPassage(points[j], end_a=points[i], end_b=points[k])
                        fractional_solution.add(vp, 1.0)
            already_visited_vertices.add(v)
        return fractional_solution


class AtomicStripMatchingTest(unittest.TestCase):
    def test1(self):
        p0 = PointVertex(1.0, 0.0)
        p1 = PointVertex(2.0, 0.0)
        graph = nx.Graph()
        graph.add_nodes_from([p0, p1])
        graph.add_edge(p0, p1)
        asm = AtomicStripMatching(
            graph,
            TransitionCostCalculator(
                SimpleTouringCosts(turn_factor=1.0, distance_factor=1.0)
            ),
        )
        s0 = asm.create_atomic_strip(p0, 0.0)
        asm.add_skip_penalty(s0, 0.1)
        s1 = asm.create_atomic_strip(p1, 2.0)
        asm.add_skip_penalty(s1, 0.0)
        s2 = asm.create_atomic_strip(p1, 1.0)
        edges = asm.solve()
        assert len(edges) == 3
        assert s0.vertices not in edges
        assert s1.vertices in edges
        assert s2.vertices not in edges
