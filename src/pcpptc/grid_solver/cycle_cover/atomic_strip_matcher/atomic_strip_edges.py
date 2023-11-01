import unittest
from collections import defaultdict

from pcpptc.utils import Point

from .atomic_strip import AtomicStrips
from .atomic_strip_vertex import AtomicStripVertex


class AtomicStripEdge:
    """
    Connecting endpoints of atomic strips.
    """

    def __init__(self, index: int, vertices: tuple, weight: float):
        self.index = index
        self.vertices = vertices
        assert len(vertices) == 2
        assert vertices[0].index <= vertices[1].index
        self.weight = weight

    def __hash__(self):
        return hash(self.vertices)

    def __eq__(self, other):
        return self.vertices == other.vertices

    def __contains__(self, item):
        return item in self.vertices

    def __iter__(self):
        yield self.vertices[0]
        yield self.vertices[1]

    def other_end(self, v):
        if v == self.vertices[0]:
            return self.vertices[1]
        elif v == self.vertices[1]:
            return self.vertices[0]
        msg = "v seems not to be in this edge"
        raise ValueError(msg)


class AtomicStripEdges:
    def __init__(self):
        self._all_edges = []
        self._incident_edges = defaultdict(list)

    def create(self, v0: AtomicStripVertex, v1: AtomicStripVertex, weight: float):
        assert weight >= 0.0
        i = len(self._all_edges)
        vertices = min(v0, v1, key=lambda v: v.index), max(
            v0, v1, key=lambda v: v.index
        )
        e = AtomicStripEdge(i, vertices, weight)
        for v in vertices:
            self._incident_edges[v].append(e)
        self._all_edges.append(e)
        assert self._all_edges[i] == e
        return e

    def edges(self, v):
        return list(self._incident_edges[v])

    def __getitem__(self, item):
        return self._all_edges[item]

    def __len__(self):
        return len(self._all_edges)

    def __iter__(self):
        yield from self._all_edges

    def contains_edge_between(self, v0: AtomicStripVertex, v1: AtomicStripVertex):
        return any(v1 in e for e in self.edges(v0))

    def get_edge_between(self, v0: AtomicStripVertex, v1: AtomicStripVertex):
        for e in self.edges(v0):
            if v1 in e:
                return e
        return None

    def __contains__(self, item):
        vertices = min(item, key=lambda v: v.index), max(item, key=lambda v: v.index)
        return any(vertices[1] in e for e in self.edges(vertices[0]))


class TestAtomicStripEdges(unittest.TestCase):
    def test_create(self):
        edges = AtomicStripEdges()
        atomic_strips = AtomicStrips()
        p0 = Point(1.0, 0.0)
        s0 = atomic_strips.create(p0, 0.0)
        s1 = atomic_strips.create(p0, 1.0)
        p1 = Point(0.0, 0.0)
        s2 = atomic_strips.create(p1, 2.0)
        s3 = atomic_strips.create(p1, 3.0)
        e = edges.create(s0.vertices[0], s0.vertices[1], 2.0)
        assert s0.vertices[0] in e
        assert s0.vertices[1] in e
        assert len(edges) == 1
        e2 = edges.create(s1.vertices[0], s2.vertices[1], 2.0)
        assert len(edges) == 2
        assert edges.edges(s0.vertices[0]) == edges.edges(s0.vertices[1])
        assert edges.edges(s0.vertices[0]) == [e]
        assert edges[0] == e
        assert edges[1] == e2
