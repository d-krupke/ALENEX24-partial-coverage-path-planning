import typing

import shapely.geometry as sgeo

from ..grid_solver.grid_instance.point import PointVertex
from ..utils import Point


class PolygonalArea:
    """
    Represents the polygonal area that has to be covered. Every point in it should be
    a feasible configuration. If not, please offset it to be.
    """

    def __init__(
        self,
        polygon: typing.Optional[sgeo.Polygon] = None,
        boundary: typing.Optional[typing.List[Point]] = None,
        holes: typing.Optional[typing.List[typing.List[Point]]] = None,
        offset: typing.Optional[float] = None,
    ):
        if polygon:
            self._shapely_polygon = polygon
        else:
            if not boundary:
                msg = "Cannot create environment without a boundary or polygon!"
                raise ValueError(
                    msg
                )
            self._shapely_polygon = sgeo.Polygon(boundary, holes)
            if offset:
                self._shapely_polygon = self._shapely_polygon.buffer(-offset)

    def as_shapely_polygon(self) -> typing.Union[sgeo.Polygon, sgeo.MultiPolygon]:
        return self._shapely_polygon

    def _iter_ring_segments(self, ring):
        coords = ring.coords
        assert len(coords) > 2
        yield from zip(coords[:-1], coords[1:])

    def segments(self):
        """
        Returns the segments of the area.
        """
        for s in self._iter_ring_segments(self._shapely_polygon.exterior):
            yield s
        for r in self._shapely_polygon.interiors:
            for s in self._iter_ring_segments(r):
                yield s

    def volume(self) -> float:
        return self._shapely_polygon.area

    def has_line_of_sight(
        self, p0: typing.Union[Point, PointVertex], p1: typing.Union[Point, PointVertex]
    ) -> bool:
        """
        Returns true if the line between the two waypoints does not intersect any segment
        of the boundary (or any holes), i.target., the whole line is contained in the area.

        TODO: Currently it just checks intersection with any segment. There should be a faster way.
        """
        s = sgeo.LineString((sgeo.Point(p0[0], p0[1]), sgeo.Point(p1[0], p1[1])))
        rings = list(self._shapely_polygon.interiors)
        rings.append(self._shapely_polygon.exterior)
        return all(not s.intersects(r) for r in rings)

    def contains(self, point: Point) -> bool:
        """
        Check if point is within the area.
        """
        p = sgeo.Point(point)
        return self._shapely_polygon.contains(p)

    def filter(
        self, points: typing.Iterable[typing.Union[Point, PointVertex]]
    ) -> typing.Iterable[typing.Union[PointVertex, Point]]:
        """
        Filters waypoints to those that are contained in the area.
        """
        for p in points:
            if self.contains(p):
                yield p

    def get_bounding_box(self):
        (min_x, min_y, max_x, max_y) = self._shapely_polygon.bounds
        return (Point(min_x, min_y), Point(max_x, max_y))
