import math
import unittest

from ...grid_instance import PointVertex


class AtomicStripVertex:
    def __init__(self, index, point_vertex: PointVertex, direction):
        """
        Do not create these yourself.
        """
        self.index = index
        self.point_vertex = point_vertex
        self.direction = direction % (2 * math.pi)

    def __hash__(self):
        return self.index

    def __eq__(self, other):
        return (self.index, self.point_vertex, self.direction) == (
            other.index,
            other.point_vertex,
            other.direction,
        )

    def __str__(self):
        return f"AtomicStripVertex({self.index}, {self.point_vertex}, {self.direction})"

    def __repr__(self):
        return str(self)


class AtomicStripVertices:
    def __init__(self):
        self._vertices = []
        self._partners = []

    def _create(self, point: PointVertex, direction: float):
        v = AtomicStripVertex(
            index=len(self._vertices), point_vertex=point, direction=direction
        )
        self._vertices.append(v)
        assert self._vertices[v.index] == v
        return v

    def create_pair(self, point: PointVertex, orientation: float):
        v0 = self._create(point, orientation)
        v1 = self._create(point, orientation + math.pi)
        self._partners.append(v1)
        self._partners.append(v0)
        assert len(self._vertices) == len(self._partners)
        return v0, v1

    def __getitem__(self, item):
        return self._vertices[item]

    def get_partner(self, v: AtomicStripVertex):
        return self._partners[v.index]

    def __len__(self):
        return len(self._vertices)

    def __str__(self):
        return str(self._vertices)


class TestAtomicStripVertices(unittest.TestCase):
    def test1(self):
        asv = AtomicStripVertices()
        p = PointVertex(1.0, 2.0)
        v0, v1 = asv.create_pair(p, 0.5 * math.pi)
        self.assertAlmostEqual(v0.direction + math.pi, v1.direction, 2)
        assert asv.get_partner(v0) == v1
        assert asv.get_partner(v1) == v0
        assert len(asv) == 2
        assert v0.point_vertex == p
        v2, v3 = asv.create_pair(p, 0.5 * math.pi)
        self.assertAlmostEqual(v2.direction + math.pi, v3.direction, 2)
        assert asv.get_partner(v2) == v3
        assert asv.get_partner(v3) == v2
        assert len(asv) == 4
