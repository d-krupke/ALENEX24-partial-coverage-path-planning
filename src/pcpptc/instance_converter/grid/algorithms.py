import abc
import math
import typing

from shapely.geometry import Point

from pcpptc.grid_solver.grid_instance import PointVertex
from pcpptc.polygon_instance import PolygonInstance

from .basic_grids import hexagonal_grid, square_grid
from .transformer import Transformer


class GridAlgorithm(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, pi: PolygonInstance, *args, **kwargs
    ) -> typing.List[PointVertex]:
        pass


class SimpleHexagonalGrid(GridAlgorithm):
    def __init__(self, distance_factor: float = (2 / math.sqrt(3)) * 2, scale=1.0):
        self.scale = scale
        self.radius_factor = distance_factor

    """
    Creates a simple hexagonal grid.
    """

    def __call__(
        self, pi: PolygonInstance, angle=0.0, translation=(0.0, 0.0), *args, **kwargs
    ) -> typing.List[PointVertex]:
        rotator = Transformer(pi.feasible_area, rotation=angle, translation=translation)
        polygon = rotator.transformed_area()
        min_x, min_y, max_x, max_y = polygon.bounds
        l = pi.tool_radius * self.scale * self.radius_factor
        min_x -= (-translation[0]) % l
        min_y -= (-translation[0]) % l
        points = hexagonal_grid(
            min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, side_length=l
        )

        points_contained = (p for p in points if polygon.contains(Point(p[0], p[1])))
        grid_points = [PointVertex(rotator.invert_point(p)) for p in points_contained]
        return grid_points


class SimpleSquareGrid(GridAlgorithm):
    """
    Creates a simple square grid.
    """

    def __init__(self, scale: float = 1.0, distance_factor: float = 2):
        self.scale = scale
        self.distance_factor = distance_factor

    def __call__(
        self, pi: PolygonInstance, angle=0.0, translation=(0.0, 0.0), *args, **kwargs
    ) -> typing.List[PointVertex]:
        rotator = Transformer(pi.feasible_area, angle, translation)
        polygon = rotator.transformed_area()
        min_x, min_y, max_x, max_y = polygon.bounds
        l = self.distance_factor * pi.tool_radius * self.scale
        min_x -= (-translation[0]) % l
        min_y -= (-translation[0]) % l
        points = square_grid(
            min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y, side_length=l
        )

        points_contained = (p for p in points if polygon.contains(Point(p[0], p[1])))
        grid_points = [PointVertex(rotator.invert_point(p)) for p in points_contained]
        return grid_points
