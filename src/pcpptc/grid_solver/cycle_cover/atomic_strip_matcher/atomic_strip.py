"""
An atomic strip is a segment with no length and only an orientation.
It has two ends represented by vertices.
The vertices have opposing direction.
We can connect these atomic strips to form a tour.
This is a matching on the ends of the atomic strips.
The atomic strips allow us to move the turn costs into the edge weights because the atomic
strips already have an orientation.
"""

import math
import unittest
from collections import defaultdict

from pcpptc.utils import Point

from ...grid_instance import PointVertex
from .atomic_strip_vertex import AtomicStripVertex, AtomicStripVertices


class AtomicStrip:
    """
    An atomic strip with two vertices in AtomicStripBlueprint.vertices at position `point_vertex`.
    It has the orientation `orientation`.
    """

    def __init__(self, point_vertex: PointVertex, orientation: float, vertices: tuple):
        self.vertices = vertices
        self.point_vertex = point_vertex
        self.orientation = orientation % (2 * math.pi)
        assert len(self.vertices) == 2, "Should have two vertices"
        assert self.vertices[0].point_vertex == self.vertices[1].point_vertex
        assert self.vertices[0].point_vertex == self.point_vertex

    def __str__(self):
        return f"AtomicStripBlueprint({self.point_vertex}, {self.orientation}): {self.vertices[0].index}<->{self.vertices[1].index}"


class AtomicStrips:
    """
    Manages the atomic strips of an polygon.
    """

    def __init__(self):
        self.vertices = AtomicStripVertices()
        self._all_strips = []
        self._strips_at_point = defaultdict(list)
        self._strip_of_vertex = []

    def create(self, point: PointVertex, orientation):
        vertices = self.vertices.create_pair(point=point, orientation=orientation)
        atomic_strip = AtomicStrip(point, orientation, vertices=vertices)
        self._all_strips.append(atomic_strip)
        self._strips_at_point[point].append(atomic_strip)
        self._strip_of_vertex.append(atomic_strip)
        assert self.get_atomic_strip_of_vertex(vertices[0]) == atomic_strip
        self._strip_of_vertex.append(atomic_strip)
        assert self.get_atomic_strip_of_vertex(vertices[1]) == atomic_strip
        return atomic_strip

    def get_atomic_strips_of_point(self, p: Point):
        return self._strips_at_point[p]

    def get_atomic_strip_of_vertex(self, v: AtomicStripVertex):
        return self._strip_of_vertex[v.index]

    def __iter__(self):
        yield from self._all_strips

    def __len__(self):
        return len(self._all_strips)


class TestAtomicStrips(unittest.TestCase):
    def test_length(self):
        atomic_strips = AtomicStrips()
        p = PointVertex(1.0, 2.0)
        atomic_strips.create(p, 0.5 * math.pi)
        atomic_strips.create(p, 0.5 * math.pi)
        atomic_strips.create(p, 0.5 * math.pi)
        atomic_strips.create(p, 0.5 * math.pi)
        assert len(atomic_strips) == 4

    def test_atomic_strips_of_point(self):
        atomic_strips = AtomicStrips()
        p = PointVertex(1.0, 2.0)
        atomic_strips.create(p, 0.5 * math.pi)
        atomic_strips.create(p, 0.5 * math.pi)
        s = atomic_strips.create(p, 0.5 * math.pi)
        assert s == atomic_strips.get_atomic_strip_of_vertex(s.vertices[0])
        atomic_strips.create(p, 0.5 * math.pi)
        p2 = PointVertex(3.0, 2.0)
        atomic_strips.create(p2, 0.5 * math.pi)
        atomic_strips.create(p2, 0.5 * math.pi)
        atomic_strips.create(p2, 0.5 * math.pi)
        atomic_strips.create(p2, 0.5 * math.pi)
        assert len(atomic_strips) == 8
        assert all(s.point_vertex == p for s in atomic_strips.get_atomic_strips_of_point(p))
        assert len(atomic_strips.get_atomic_strips_of_point(p)) == 4

    def test_right_point_and_orientations(self):
        atomic_strips = AtomicStrips()
        p = Point(1.0, 2.0)
        s = atomic_strips.create(p, math.pi)
        assert p == s.vertices[0].point_vertex
        assert p == s.vertices[1].point_vertex
        self.assertAlmostEqual(math.pi, s.vertices[0].direction, 2)
        self.assertAlmostEqual(0.0, s.vertices[1].direction, 2)
