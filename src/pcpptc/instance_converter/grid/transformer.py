import typing

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon


class Transformer:
    def __init__(
        self,
        polygon: Polygon,
        rotation: float = 0.0,
        translation: typing.Tuple[float, float] = (0.0, 0.0),
    ):
        self.polygon = polygon
        self.rotation = rotation
        self.translation = translation
        self.center = polygon.centroid

    def _rotate(self, polygon):
        if self.rotation:
            return rotate(
                polygon, angle=self.rotation, use_radians=True, origin=self.center
            )
        else:
            return self.polygon

    def _rotate_back(self, p: typing.Tuple[float, float]) -> typing.Tuple[float, float]:
        if self.rotation:
            p = Point(p[0], p[1])
            p_rotated = rotate(
                p, angle=-self.rotation, use_radians=True, origin=self.center
            )
            return p_rotated.x, p_rotated.y
        else:
            return p

    def _translate(self, polygon):
        return translate(polygon, self.translation[0], self.translation[1])

    def _translate_back(
        self, p: typing.Tuple[float, float]
    ) -> typing.Tuple[float, float]:
        return p[0] - self.translation[0], p[1] - self.translation[1]

    def transformed_area(self) -> Polygon:
        return self._translate(self._rotate(self.polygon))

    def invert_point(self, p: typing.Tuple[float, float]) -> typing.Tuple[float, float]:
        return self._rotate_back(self._translate_back(p))
