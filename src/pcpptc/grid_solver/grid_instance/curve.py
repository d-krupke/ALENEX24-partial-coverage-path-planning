import typing

from .point import PointVertex


class Curve:
    """A curve that can be represented as an edge to save computation time."""

    def __init__(self, points: typing.Iterable[PointVertex]):
        self.points: typing.List[PointVertex] = list(points)

    def connecting_point(self, end_vertex: PointVertex) -> PointVertex:
        if end_vertex == self.points[0]:
            return self.points[1]
        elif end_vertex == self.points[-1]:
            return self.points[-2]
        msg = "No matching point."
        raise ValueError(msg)
