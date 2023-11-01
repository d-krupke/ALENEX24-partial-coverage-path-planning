import random

import shapely.affinity
from shapely.geometry import Point, Polygon

from .angles import turn_angle


class RandomThickQuadrangleGenerator:
    def __init__(
        self, mean: float, std: float, min_angle: float, min_side_length: float
    ):
        self.mean = mean
        self.std = std
        self.min_angle = min_angle
        self.min_side_length = min_side_length
        self.max_tries = 10

    def _random_side_length(self) -> float:
        x = random.gauss(self.mean, self.std)
        return max(x, self.min_side_length)

    def _random_base_rectangle(self) -> Polygon:
        height = self._random_side_length()
        width = self._random_side_length()
        return Polygon(
            [
                Point(-0.5 * width, -0.5 * height),
                Point(0.5 * width, -0.5 * height),
                Point(0.5 * width, 0.5 * height),
                Point(-0.5 * width, 0.5 * height),
            ]
        )

    def _random_shift_point(self, p: Point, std: float) -> Point:
        return Point(p.x + random.gauss(0.0, std), p.y + random.gauss(0.0, std))

    def _min_side_length(self, p: Polygon) -> float:
        coords = [Point(x[0], x[1]) for x in p.exterior.coords]
        return min(point.distance(coords[i + 1]) for i, point in enumerate(coords[:-1]))

    def _min_angle(self, p: Polygon) -> float:
        coords = [Point(x[0], x[1]) for x in p.exterior.coords]
        return min(
            turn_angle(
                coords[(i - 1) % len(coords)], point, coords[(i + 1) % len(coords)]
            )
            for i, point in enumerate(coords[:-1])
        )

    def _random_shift_points(self, p: Polygon) -> Polygon:
        std = 0.1 * (self._min_side_length(p) - self.min_side_length)
        coords = [Point(x[0], x[1]) for x in p.exterior.coords][:-1]
        points = [self._random_shift_point(point, std) for point in coords]
        return Polygon(points)

    def _random_rotate(self, p: Polygon) -> Polygon:
        return shapely.affinity.rotate(p, random.random() * 180)

    def __call__(self, center: Point) -> Polygon:
        for _i in range(self.max_tries):
            p = self._random_base_rectangle()
            p_ = self._random_shift_points(p)
            if (
                self._min_side_length(p_) >= self.min_side_length
                and self._min_angle(p_) >= self.min_angle
            ):
                return shapely.affinity.translate(
                    self._random_rotate(p_), center.x, center.y
                )
        return shapely.affinity.translate(
            self._random_rotate(self._random_base_rectangle()), center.x, center.y
        )


class RandomThickPolygonGenerator:
    def __init__(
        self,
        n_quadrangles: int,
        quadrangle_generator: RandomThickQuadrangleGenerator,
        boundary_union: bool = True,
    ):
        self.n_quadrangles = n_quadrangles
        self.quadrangle_gen = quadrangle_generator
        self.use_boundary_points = boundary_union

    def _get_merge_point(self, p: Polygon) -> Point:
        bounds = p.bounds
        if self.use_boundary_points:
            for _i in range(10):
                x = bounds[0] + random.random() * (bounds[2] - bounds[0])
                y = bounds[1] + random.random() * (bounds[3] - bounds[1])
                point = Point(x, y)
                if p.contains(point):
                    return point
        coords = list(p.exterior.coords)
        return Point(random.choice(coords))

    def __call__(self, *args, **kwargs) -> Polygon:
        p = self.quadrangle_gen(Point(0.0, 0.0))
        for _i in range(self.n_quadrangles - 1):
            c = self._get_merge_point(p)
            p = p.union(self.quadrangle_gen(c))
        return p


class RandomThickPolygonInPolygonGenerator:
    def __init__(
        self, rand_thick_quadrangle_gen: RandomThickQuadrangleGenerator, n: int = 3
    ):
        self.rand_quad = rand_thick_quadrangle_gen
        self.n = n

    def _get_random_point(self, p: Polygon) -> Point:
        bounds = p.bounds
        for _i in range(10):
            x = bounds[0] + random.random() * (bounds[2] - bounds[0])
            y = bounds[1] + random.random() * (bounds[3] - bounds[1])
            point = Point(x, y)
            if p.contains(point):
                return point
        coords = list(p.exterior.coords)
        return Point(random.choice(coords))

    def __call__(self, polygon: Polygon) -> Polygon:
        p = self.rand_quad(self._get_random_point(polygon))
        for _i in range(self.n - 1):
            p = p.union(self.rand_quad(self._get_random_point(p)))
        return p.intersection(polygon)
