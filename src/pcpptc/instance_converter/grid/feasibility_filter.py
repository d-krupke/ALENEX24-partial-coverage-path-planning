import typing

import shapely.geometry
from optimizer.grid_solver.grid_instance import PointVertex


class FeasibilityFilter:
    def __init__(self, area: shapely.geometry.Polygon):
        self.feasible_area = area

    def __call__(self, points: typing.Iterable[PointVertex]):
        for p in points:
            if self.feasible_area.contains(shapely.geometry.Point(p.x, p.y)):
                yield p
