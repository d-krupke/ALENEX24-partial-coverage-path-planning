import math
import typing

import numpy as np
from shapely.geometry import LinearRing
from sympy import Point

from pcpptc.grid_solver.grid_instance import PointVertex

from ...polygon_instance import PolygonInstance

_POINT_BASED_D = 3 / math.sqrt(3)
_EDGE_BASED_D = 4 / math.sqrt(3)


class BoundaryGrid:
    def __init__(
        self, reduction_factor: float = 0.03, distance_factor: float = _EDGE_BASED_D
    ):
        self.distance_factor = distance_factor
        self.reduction_factor = reduction_factor

    def _boundaries(self, instance: PolygonInstance) -> typing.Iterable[LinearRing]:
        offset = self.reduction_factor * instance.tool_radius
        slightly_reduced_boundary = instance.feasible_area.buffer(-offset)
        yield slightly_reduced_boundary.exterior
        yield from slightly_reduced_boundary.interiors

    def _points_between(
        self, p0: Point, p1: Point, target_dist: float
    ) -> typing.Iterable[Point]:
        d = p0.distance(p1)
        if target_dist >= d:
            return None  # Nothing to do
        n_segments = math.ceil(d / target_dist)
        l_segment = d / (n_segments)
        p0 = np.array([p0.x, p0.y])
        p1 = np.array([p1.x, p1.y])
        step = l_segment * ((p1 - p0) / d)
        for i in range(1, n_segments):
            p = p0 + i * step
            yield Point(p[0], p[1])

    def _points_on_ring(self, boundary: LinearRing, max_dist: float):
        points = [Point(*p) for p in boundary.coords]
        for i, p in enumerate(points):
            yield p
            p_end = points[(i + 1) % len(points)]
            for p_ in self._points_between(p, p_end, max_dist):
                yield p_

    def __call__(self, instance: PolygonInstance) -> typing.Iterable[PointVertex]:
        for boundary in self._boundaries(instance):
            for p in self._points_on_ring(
                boundary, instance.tool_radius * self.distance_factor
            ):
                yield PointVertex(p)
