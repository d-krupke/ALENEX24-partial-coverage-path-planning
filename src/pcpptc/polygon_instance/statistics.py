import json
import typing

import numpy as np
from shapely.geometry import Point, Polygon

from .instance import PolygonInstance


class InstanceStatistics:
    def __init__(self, instance: PolygonInstance):
        self.instance = instance

    def resize_polygon_to_tool(self, polygon: Polygon) -> Polygon:
        def resize_point(p: Point) -> Point:
            return Point(p.x * (1.0 / self.instance.tool_radius))

        return Polygon(
            [resize_point(p) for p in polygon.exterior.coords],
            holes=[
                [resize_point(p) for p in hole.coords] for hole in polygon.interiors
            ],
        )

    def normalize_to_tool(self, instance: PolygonInstance) -> PolygonInstance:
        scale = self.resize_polygon_to_tool
        pi = PolygonInstance(
            feasible_area=scale(instance.feasible_area),
            expensive_areas=[(scale(p), v) for p, v in instance.expensive_areas],
            valuable_areas=[
                (scale(p), v * (p.area / scale(p).area))
                for p, v in instance.valuable_areas
            ],
            turn_cost=instance.turn_cost,
            distance_cost=instance.distance_cost / instance.tool_radius,
            tool_radius=1.0,
        )
        return pi

    def describe_sequence(self, seq: typing.Iterable[float]) -> dict:
        a = np.array(list(seq))
        not_empty = len(a) > 0
        return {
            "min": a.min() if not_empty else None,
            "max": a.max() if not_empty else None,
            "mean": a.mean() if not_empty else None,
            "std": a.std() if not_empty else None,
            "sum": a.sum() if not_empty else 0.0,
            "n": len(a),
        }

    def as_json(self, as_string=False) -> typing.Union[dict, str]:
        fa = self.instance.feasible_area
        area = fa.area
        enclosed_area = Polygon(fa.exterior).area
        perimeter = fa.exterior.length
        perimeter_vertices = len(fa.exterior.coords)
        holes = self.describe_sequence(Polygon(p).area for p in fa.interiors)

        data = {
            "area": area,
            "perimeter": perimeter,
            "perimeter_vertices": perimeter_vertices,
            "holes": holes,
            "relative_hole_area": holes["sum"] / enclosed_area,
            "tool_radius": self.instance.tool_radius,
        }
        if as_string:
            return json.dumps(data)
        else:
            return data
