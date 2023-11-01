import random
import typing
import unittest

import networkx as nx

from pcpptc.utils import distance, turn_angle

from ..grid_instance import PointVertex
from ..grid_instance.vertex_passage import VertexPassage
from .create_minimal_instance import create_minimal_graph_from_solution
from .feasibility import (
    are_all_passages_between_neighbors,
    is_flow_feasible,
    is_integral,
)
from .fractional_solution import FractionalSolution


class Cycle:
    def __init__(self, passages: typing.List[VertexPassage]):
        self.passages = passages

    def is_connected(self) -> bool:
        for i in range(len(self.passages) - 1):
            if self.passages[i + 1].v not in self.passages[i].endpoints():
                return False
            if self.passages[i].v not in self.passages[i + 1].endpoints():
                return False
        if self.passages[-1].v not in self.passages[0].endpoints():
            return False
        if self.passages[0].v not in self.passages[-1].endpoints():
            return False
        return True

    def covered_vertices(self) -> typing.Dict[PointVertex, int]:
        coverage = {}
        for vp in self.passages:
            coverage[vp.v] = 1 + coverage.get(vp.v, 0)
        return coverage

    def waypoints(self) -> typing.List[PointVertex]:
        return list(self.iterate_vertices())

    def iterate_vertices(
        self, closed=False, double_closed=False
    ) -> typing.Iterable[PointVertex]:
        if double_closed:
            yield self.passages[-1].v
            for v in self.iterate_vertices(closed=True):
                yield v
        elif closed:
            for v in self.iterate_vertices():
                yield v
            yield self.passages[0].v
        else:
            for vp in self.passages:
                yield vp.v

    def edges(self) -> typing.Dict[typing.Tuple[PointVertex, PointVertex], int]:
        edges = {}
        vertex_chain = list(self.iterate_vertices(closed=True))
        for i in range(len(vertex_chain) - 1):
            vertex_pair = (vertex_chain[i], vertex_chain[i + 1])
            e = (min(vertex_pair), max(vertex_pair))
            edges[e] = 1 + edges.get(e, 0)
        return edges

    def length(self) -> float:
        chain = list(self.iterate_vertices(closed=True))
        l = 0.0
        for v, w in zip(chain[:-1], chain[1:]):
            l += distance(v, w)
        return l

    def angle_sum(self) -> float:
        chain = list(self.iterate_vertices(double_closed=True))
        l = 0.0
        for u, v, w in zip(chain[:-2], chain[1:-1], chain[2:]):
            l += turn_angle(u, v, w)
        return l

    def to_fractional_solution(self) -> FractionalSolution:
        fs = FractionalSolution()
        chain = list(self.iterate_vertices(double_closed=True))
        for u, v, w in zip(chain[:-2], chain[1:-1], chain[2:]):
            vp = VertexPassage(v, end_a=u, end_b=w)
            fs.add(vp, 1.0)
        assert sum(x for vp, x in fs) == len(self.passages)
        return fs

    def __len__(self):
        return len(self.passages)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return (
            f"Cycle[{hash(self)}]({', '.join(str(v) for v in self.iterate_vertices())})"
        )

    def __repr__(self):
        return f"Cycle({hash(self)})"

    def __getitem__(self, item):
        return self.passages[item % len(self)].v

    def __bool__(self):
        return len(self.passages) > 0


class CycleTest(unittest.TestCase):
    def cycles_to_frac(self, cc):
        fs = FractionalSolution()
        for c in cc:
            for i, p in enumerate(c):
                fs.add(
                    VertexPassage(
                        end_a=c[(i - 1) % len(c)], v=p, end_b=c[(i + 1) % len(c)]
                    ),
                    1.0,
                )
        return fs

    def points(self, n):
        return [PointVertex(random.random(), random.random()) for i in range(n)]

    def test_fractional_solution(self):
        p0 = PointVertex(0.0, 0.0)
        p1 = PointVertex(1.0, 1.0)
        p2 = PointVertex(2.0, 0.0)
        frac_sol = FractionalSolution()
        frac_sol[VertexPassage(p0, p1, p2)] = 1.0
        frac_sol[VertexPassage(p1, p2, p0)] = 1.0
        frac_sol[VertexPassage(p2, p0, p1)] = 1.0
        graph = create_minimal_graph_from_solution(frac_sol)
        cc = create_cycle_solution(graph, fractional_solution=frac_sol)
        assert len(cc) == 1
        assert len(cc[0]) == 3

    def test_eight(self):
        points = self.points(6)
        fs = self.cycles_to_frac(
            [
                [
                    points[0],
                    points[1],
                    points[2],
                    points[3],
                    points[4],
                    points[1],
                    points[2],
                    points[5],
                ]
            ]
        )
        graph = create_minimal_graph_from_solution(fs)
        cc = create_cycle_solution(graph, fractional_solution=fs)
        assert len(cc) == 1
        assert len(cc[0]) == 8

    def test_double_eight(self):
        points = self.points(6)
        fs = self.cycles_to_frac(
            [
                [
                    points[0],
                    points[1],
                    points[2],
                    points[3],
                    points[4],
                    points[1],
                    points[2],
                    points[5],
                    points[0],
                    points[1],
                    points[2],
                    points[3],
                    points[4],
                    points[1],
                    points[2],
                    points[5],
                ]
            ]
        )
        graph = create_minimal_graph_from_solution(fs)
        cc = create_cycle_solution(graph, fractional_solution=fs)
        assert len(cc) == 1
        assert len(cc[0]) == 16

    def test_loop(self):
        loops = 4
        points = self.points(6 + 2 * loops)
        fs = self.cycles_to_frac(
            [[points[0], points[1], points[2], points[3], points[4], points[5]]]
            + [
                [points[0], points[1], points[6 + 2 * i], points[7 + 2 * i]]
                for i in range(loops)
            ]
        )
        graph = create_minimal_graph_from_solution(fs)
        cc = create_cycle_solution(graph, fractional_solution=fs)
        assert len(cc) == 1
        assert len(cc[0]) == 6 + 4 * loops

    def test_two_loop(self):
        loops = 4
        loops_b = 4
        points = self.points(6 + 2 * loops)
        fs = self.cycles_to_frac(
            [[points[0], points[1], points[2], points[3], points[4], points[5]]]
            + [
                [points[0], points[1], points[6 + 2 * i], points[7 + 2 * i]]
                for i in range(loops)
            ]
            + [
                [points[3], points[4], points[6 + 2 * i], points[7 + 2 * i]]
                for i in range(loops_b)
            ]
        )
        graph = create_minimal_graph_from_solution(fs)
        cc = create_cycle_solution(graph, fractional_solution=fs)
        assert len(cc) == 1
        assert len(cc[0]) == 6 + 4 * loops + 4 * loops_b

    def test_two(self):
        points = self.points(2)
        fs = self.cycles_to_frac([[points[0], points[1], points[0], points[1]]])
        graph = create_minimal_graph_from_solution(fs)
        cc = create_cycle_solution(graph, fractional_solution=fs)
        assert len(cc) == 1
        assert len(cc[0]) == 4


class VertexPassageSet:
    """
    A multi-set of vertex passages from a solution.
    The solution should be approximately integral (the maximal rounding can be specified).
    Allows to iterate nicely through the passages.
    """

    def __init__(
        self, graph: nx.Graph, fractional_solution: FractionalSolution, eps: float = 0.1
    ):
        self.graph = graph
        self._counts = {}
        for vp, x in fractional_solution:
            n = round(x)
            if abs(n - x) > eps:
                msg = f"Cannot round {x}. Above epsilon."
                raise ValueError(msg)
            if n > 0:
                self._counts[vp] = n

    def pop(self, vp: VertexPassage) -> int:
        n = self._counts[vp]
        n -= 1
        assert n >= 0, "Should always be positive"
        if n == 0:
            self._counts.pop(vp)
        else:
            self._counts[vp] = n
        return n

    def next(
        self, current_vertex: PointVertex, previous_vertex: PointVertex
    ) -> typing.Optional[PointVertex]:
        if current_vertex == previous_vertex:
            msg = "Current vertex cannot be previous."
            raise ValueError(msg)
        for v in self.graph.neighbors(current_vertex):
            assert v != current_vertex, "Cannot be neighbord to itself"
            vp = VertexPassage(v=current_vertex, end_a=previous_vertex, end_b=v)
            if vp in self._counts:
                return v
        return None

    def any_remaining(self) -> typing.Optional[VertexPassage]:
        for vp, _x in self._counts.items():
            return vp
        return None

    def is_empty(self) -> bool:
        return len(self._counts) == 0


def _collect_cycle(
    remaining_passages: VertexPassageSet, v: PointVertex, prev: PointVertex
) -> typing.Iterable[VertexPassage]:
    start_v = v
    start_prev = prev
    while True:
        n = remaining_passages.next(v, prev)
        if n:
            vp = VertexPassage(v=v, end_a=prev, end_b=n)
            remaining_passages.pop(vp)
            yield vp
            prev = v
            v = n
        else:
            assert prev == start_prev and v == start_v, "Should be a cycle"
            assert remaining_passages.next(start_v, start_prev) is None
            return


def create_cycle_solution(
    graph: nx.Graph, fractional_solution: FractionalSolution
) -> typing.List[Cycle]:
    """
    Create from a nearly-integral fractional solution a list of cycles.
    A cycle_cover itself is a list of consecutive vertex passages.
    E.g. [[(v0, v1, v0), (v1, v0, v1)]]

    You can access the vertices behind them by
    ```
    cc = create_cycle_solution(polygon, fractional_solution)
    cc = [[vp.v for vp in cycle_cover] for cycle_cover in cc]
    ```

    It will not repeat vertices. You have to close the cycle_cover by yourself.
    """
    remaining_passages = VertexPassageSet(graph, fractional_solution)
    cycles = []
    assert are_all_passages_between_neighbors(graph, fractional_solution)
    assert is_flow_feasible(fractional_solution, raise_exception=True)
    assert is_integral(fractional_solution)

    while not remaining_passages.is_empty():
        vp = remaining_passages.any_remaining()
        stack = list(_collect_cycle(remaining_passages, vp.v, vp.end_b))
        assert (
            len(stack) >= 2
        ), "Stack should be filled with at least two vertex passages"
        assert (
            remaining_passages.next(stack[0].v, stack[-1].v) is None
        ), "Should not be greedily extensible"
        cycle = []
        while len(stack) >= 2:
            # only happens rarely. Needs multi-coverage to happen which many instances don't need.
            assert Cycle(cycle + stack[::-1]).is_connected()
            subcycle = list(
                _collect_cycle(remaining_passages, v=stack[-1].v, prev=stack[-2].v)
            )
            cycle.append(stack.pop())
            assert Cycle(cycle + subcycle[::-1] + stack[::-1]).is_connected()
            if subcycle:
                assert Cycle(subcycle).is_connected()
                for _i, vp in enumerate(subcycle):
                    stack.append(vp)
                assert Cycle(cycle + stack[::-1]).is_connected()
                assert subcycle[-1] == stack[-1]
                assert subcycle[-2] == stack[-2]
            assert cycle[-1] in fractional_solution
        if stack:
            cycle.append(stack.pop())
        assert len(stack) == 0, "Should be empty"
        assert len(cycle) >= 2
        cycle = Cycle(cycle)
        assert cycle.is_connected(), "Created cycle_cover should be connected"
        cycles.append(cycle)
        assert all(
            remaining_passages.next(cycle[i], cycle[i + 1]) is None
            for i in range(len(cycle))
        )
    return cycles
