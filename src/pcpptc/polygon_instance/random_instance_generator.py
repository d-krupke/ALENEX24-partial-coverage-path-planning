import math
import random

import shapely.ops
from shapely.geometry import MultiPolygon, Polygon

from .instance import PolygonInstance
from .thick_polygon_generator import (
    RandomThickPolygonGenerator,
    RandomThickPolygonInPolygonGenerator,
    RandomThickQuadrangleGenerator,
)


class RandomPolygonInstanceGenerator:
    def __init__(
        self,
        complexity: float,
        size: float,
        turn_costs: float,
        tool_radius: float,
        penalties: float = 0.0,
        penalty_strength: float = 1.0,
        multiplier_strength: float = 0.0,
        multiplier: float = 0.0,
        holes: float = 1.0,
        hole_complexity: float = 1,
        hole_size: float = 1.0,
    ):
        self.complexity = complexity
        self.size = size
        self.penalties = penalties
        self.penalty_strength = penalty_strength
        self.multiplier = multiplier
        self.multiplier_strength = multiplier_strength
        self.turn_costs = turn_costs
        self.tool_radius = tool_radius
        self.holes = holes
        self.hole_size = hole_size
        self.hole_complexity = hole_complexity

    def _rand(self, v: float, lb=0.0, dev=0.1) -> int:
        if v == 0.0:
            return 0
        return int(max(lb, round(random.gauss(v, v * dev))))

    def __call__(self, *args, **kwargs):
        compl = self._rand(self.complexity, lb=1.0)
        size = self._rand(self.size, lb=1.0)
        gen1 = RandomThickQuadrangleGenerator(
            size, 0.2 * size, 0.4 * math.pi, 3 * self.tool_radius
        )
        gen2 = RandomThickQuadrangleGenerator(
            0.5 * size, 0.2 * size, 0.4 * math.pi, 3 * self.tool_radius
        )
        gen3 = RandomThickQuadrangleGenerator(
            max(4 * self.tool_radius, self.hole_size * 0.3 * size),
            0.3 * 0.3 * self.hole_size * size,
            0.25 * math.pi,
            3 * self.tool_radius,
        )
        outer = RandomThickPolygonGenerator(compl, gen1)()
        hole_gen = RandomThickPolygonInPolygonGenerator(
            gen3, self._rand(self.hole_complexity, lb=1)
        )
        for _i in range(self._rand(self.holes, 0.0, dev=0.2 * self.holes)):
            hole = hole_gen(outer)
            if outer.exterior.distance(hole) > self.tool_radius * 4:
                outer = outer.difference(hole)

        feasible_area = outer.buffer(-self.tool_radius, resolution=4)
        original_area = outer

        inner_gen = RandomThickPolygonInPolygonGenerator(gen2, 3)
        multiplier_polys = [
            inner_gen(feasible_area) for _ in range(self._rand(self.multiplier))
        ]
        multipoly = shapely.ops.unary_union(multiplier_polys)
        if type(multipoly) is Polygon:
            multiplier_polys = [multipoly]
        else:
            assert type(multipoly) is MultiPolygon
            multiplier_polys = list(multipoly.geoms)
            assert all(type(poly) is Polygon for poly in multiplier_polys)
        multipliers = [
            (
                poly,
                self._rand(self.multiplier_strength, lb=1.0, dev=0.5),
            )
            for poly in multiplier_polys
        ]
        if self.penalties == 0:
            penalties = [(outer, self.penalty_strength)]
        else:
            penalties = [
                (inner_gen(outer), self._rand(self.penalty_strength, lb=1.0, dev=0.5))
                for _ in range(self._rand(self.penalties))
            ]
        return PolygonInstance(
            feasible_area=feasible_area,
            original_area=original_area,
            expensive_areas=multipliers,
            valuable_areas=penalties,
            turn_cost=self.turn_costs,
            distance_cost=1.0,
            tool_radius=self.tool_radius,
        )
