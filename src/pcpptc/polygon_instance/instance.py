import json
import math
import typing

import numpy as np
import shapely.geometry as sly
from shapely.errors import TopologicalError
from shapely.geometry import MultiPolygon

from .angles import turn_angle
from .polygon_json import polygon_from_json, polygon_to_json


class PolygonInstance:
    """
    The polygon polygon is a close representation of the real world problem before
    being converted to an auxiliary problem. It represents a very simplified, polygonal
    world. The tool is a circle and covers perfectly. All areas are represented as
    polygons.
    * The most important polygon is the polygon that describes the feasible area.
        It contains all waypoints where the center of the tool could move (in case of a room,
        this would be the room minus the tool radius as offset.
    * Next, we have multiplier areas, that multiply the touring cost while the center of
        the tool is within it. If multiple such polygons overlap, the product of the
        corresponding multiplier is used.
    * Last, we have the penalty areas. It describes the prize or penalty for covering
        it or skipping it. If there are no penalty areas, no tour is the optimal solution.
        The higher the value, the more urgent it should be covered. If two such polygons
        overlap, the sum is used. The prize/penalty of such a polygon is the area of the
        intersection of the coverage with it times the penalty value. The penalty value
        hence is penalty per area and is not the penalty or prize of covering the full
        polygon.

    The polygons should be simplified and not to thin. Otherwise, the result can be
    faulty. For efficient evaluation, the accuracy is reduced. Perfect evaluation would
    be very expensive.

    Why is the penalty area based on area-intersection and multiplier area based on
    inclusion of the path?
    Because the second version allows to punish multiple passages while area intersection
    only considers the first passage. This is a good choice for rewarding cleaning or
    mowing an area but a bad choice if passing this area is simply expensive.
    """

    def __init__(
        self,
        feasible_area: sly.Polygon,
        valuable_areas: typing.List[typing.Tuple[sly.Polygon, float]],
        turn_cost: float,
        expensive_areas: typing.Optional[
            typing.List[typing.Tuple[sly.Polygon, float]]
        ] = None,
        original_area: typing.Optional[sly.Polygon] = None,
        distance_cost: float = 1.0,
        tool_radius: float = 0.5,
    ):
        """
        * feasible_area: A polygon that includes all valid positions for a circle tool
                        with radius `tool_radius`. The position of the tool are the
                        coordinates of the center.
        * expensive_areas: Tuples of a polygon and a value. The costs of the part of a
                        tour that is included in such a polygon is multiplied by
                        the value. Multiplicative if overlapping.
        * valuable_areas: Tuples of a polygon and a value. The area of such a polygon that
                        is not covered by the tour is multiplied with the value and added
                        as penalty cost. The covered area of a tour is defined by moving
                        a circle with radius `tool_radius` along the tour.
        * turn_cost: The cost of a turn is defined as its angle in radian times this
                        factor. If the turn is within a multiplier area, it is
                        additionally multiplied by the multiplier
        * original_area: The original area to be covered. Just for visualization purposes.
        * distance_cost: The cost of a segment in a tour is defined by its length times
                        this factor. If the segment is (partially) within a multiplier
                        area, the cost is (partially) multiplied by the multiplier.
        * tool_radius: The tool radius defines the radius of the circle tool for which
                        the tour is computed. The feasible_area should already include
                        the tool radius.
        """
        self.original_area = original_area
        self.feasible_area = (
            feasible_area  # The area in which the tour polygon is allowed to be.
        )
        if type(self.feasible_area) is MultiPolygon:
            msg = "Feasible area is not connected."
            raise ValueError(msg)
        if expensive_areas:
            self.expensive_areas = list(
                self._split_multipolygons(expensive_areas)
            )  # The cost of the subtour in such an area is multiplied.
        else:
            self.expensive_areas = []
        self.valuable_areas = list(
            self._split_multipolygons(valuable_areas)
        )  # Not visiting a part of this area induces a penalty equaling the missed area.
        self.distance_cost = distance_cost
        self.turn_cost = turn_cost
        self.tool_radius = tool_radius

    def _split_multipolygons(self, l):
        for poly, val in l:
            if poly.geom_type != "Polygon":
                for p in poly:
                    yield p, val
            else:
                yield poly, val

    def get_multiplier_at(self, p: sly.Point) -> float:
        """
        Returns the cost multiplier at a point
        """
        multiplier = 1.0
        for area, v in self.expensive_areas:
            area: sly.Polygon
            if area.contains(p):
                multiplier *= v
        return multiplier

    def get_multiplier_over_segment(
        self, p0: sly.Point, p1: sly.Point, resolution: typing.Optional[float] = None
    ) -> float:
        """
        Returns an estimate of the multiplier for the distance cost of a segment.
        """
        multiplier = 0.0
        if not resolution:
            resolution = 0.25 * self.tool_radius
        dist = p0.distance(p1)
        if dist <= 1e-5 * resolution:
            return (self.get_multiplier_at(p0) + self.get_multiplier_at(p1)) / 2
        samples = math.ceil(dist / resolution) - 1
        assert samples >= 0
        sample_dist = dist / (samples + 1)
        multiplier += (0.5 * sample_dist / dist) * self.get_multiplier_at(p0)
        multiplier += (0.5 * sample_dist / dist) * self.get_multiplier_at(p1)
        if samples:
            def to_np(p):
                return np.array([p.x, p.y])
            p = to_np(p0)
            step = (to_np(p1) - to_np(p0)) / dist
            for _ in range(samples):
                p += step
                multiplier += (sample_dist / dist) * self.get_multiplier_at(
                    sly.Point(p[0], p[1])
                )
        return multiplier

    def cost_of_turn(self, origin: sly.Point, turn_point: sly.Point, target: sly.Point):
        """
        Returns the cost of a turn at `turn_point` coming from `origin` and heading for
        `target`. As the cost should be symmetric, `origin` and `target` can be exchanged.
        """
        angle = turn_angle(origin, turn_point, target)
        return self.get_multiplier_at(turn_point) * self.turn_cost * angle

    def compute_touring_cost(self, coords: typing.List[sly.Point]) -> float:
        """
        Computes the touring cost (distance and turns) of a full tour.
        The tour should be provided as a list of waypoints. This list should not be closed,
        i.e., coords[0] <-> coords[-1] is a valid segment (coords[0]!=coords[-1]).
        """
        if not coords:
            return 0.0
        if coords[0] == coords[-1]:
            msg = "Coordinate list of tour should not be closed!"
            raise ValueError(msg)
        turn_costs = sum(
            self.cost_of_turn(
                coords[(i - 1) % len(coords)], p, coords[(i + 1) % len(coords)]
            )
            for i, p in enumerate(coords)
        )
        distance_costs = sum(
            self.cost_of_segment(p, coords[(i + 1) % len(coords)])
            for i, p in enumerate(coords)
        )
        return turn_costs + distance_costs

    def get_intersected_penalty_polygons(
        self, p: sly.Point
    ) -> typing.Iterable[typing.Tuple[sly.Polygon, float]]:
        """
        Returns all penalty polygons and associated penalties for a point `p`.
        """
        for penalty_poly, v in self.valuable_areas:
            if penalty_poly.contains(p):
                yield penalty_poly, v

    def compute_covering_value(self, coords: typing.List[sly.Point]) -> float:
        """
        Computes the covering value for a tour. The covering value is the sum of the
        covered areas of penalty areas times the associated penalty (penalty and prize
        are interchangeable, like opportunity loss).
        The maximal achievable value is the sum of all penalty areas times their penalty.
        The missing value is the penalty, also provided by
        `compute_missed_covering_value`.
        """
        if not coords:
            return 0.0
        covering_polygon = self.compute_covering_area(coords)
        covering_value = 0.0
        for p, value in self.valuable_areas:
            try:
                covered_area = covering_polygon.intersection(p).area
            except TopologicalError as te:
                print("Topological problems. Trying workaround...")
                covered_area = (
                    self.compute_covering_area(coords, scale=1.01).intersection(p).area
                )
            covering_value += value * covered_area
        return covering_value

    def compute_value_of_area(self, area: sly.Polygon):
        covering_value = 0.0
        for p, value in self.valuable_areas:
            covered_area = area.intersection(p).area
            covering_value += value * covered_area
        return covering_value

    def compute_covering_area(
        self, coords: typing.List[sly.Point], scale: float = 1.0
    ) -> sly.Polygon:
        """
        scale is used due for some possible problems with geometric topology
        """
        if not coords:
            msg = "Cannot compute area polygon of empty tour."
            raise ValueError(msg)
        line = sly.LineString([*coords, coords[0]])
        covering_polygon = line.buffer(
            self.tool_radius * scale, cap_style=1, join_style=1
        )
        return covering_polygon

    def compute_missed_covering_value(self, coords: typing.List[sly.Point]) -> float:
        """
        See `compute_covering_value`.
        """
        return sum(
            p.area * value for p, value in self.valuable_areas
        ) - self.compute_covering_value(coords)

    def cost_of_segment(
        self, p0: sly.Point, p1: sly.Point, resolution: typing.Optional[float] = None
    ) -> float:
        """
        Estimates the cost of a segment. This is its length times the multiplier.
        The multiplier is estimated by sampling over the given resolution.
        The resolution equals the maximum sample distance.
        By default it is set to 25% of the tool radius.
        """
        dist = p0.distance(p1)
        return (
            dist
            * self.get_multiplier_over_segment(p0, p1, resolution)
            * self.distance_cost
        )

    def to_json(
        self, file_path: typing.Optional[str] = None, as_string: bool = True
    ) -> typing.Union[str, dict]:
        """
        Computes a json representation of the polygon for storing.
        * file_path: If used, the polygon will directly written to file.
        * as_string: If true, a string is returned. Otherwise, a dict.
        """
        data = {
            "feasible_area": polygon_to_json(self.feasible_area, as_string=False),
            "expensive_areas": [
                {"polygon": polygon_to_json(p, as_string=False), "multiplier": v}
                for p, v in self.expensive_areas
            ],
            "valuable_areas": [
                {"polygon": polygon_to_json(p, as_string=False), "penalty": v}
                for p, v in self.valuable_areas
            ],
            "touring_costs": {"distance": self.distance_cost, "turn": self.turn_cost},
            "tool_radius": self.tool_radius,
        }
        if self.original_area:
            data["original_area"] = polygon_to_json(self.original_area, as_string=False)
        if file_path:
            with open(file_path, "w") as f:
                json.dump(data, f)
        if as_string:
            return json.dumps(data)
        else:
            return data

    @staticmethod
    def from_json(
        data: typing.Optional[dict] = None,
        data_string: typing.Optional[str] = None,
        file_path: typing.Optional[str] = None,
    ):
        """
        Reads a polygon polygon from json. Multiple data types are supported.
        """
        if file_path:
            with open(file_path) as f:
                data = json.load(f)
        elif data_string:
            data = json.loads(data_string)
        return PolygonInstance(
            feasible_area=polygon_from_json(data=data["feasible_area"]),
            original_area=polygon_from_json(data=data["original_area"])
            if "original_area" in data
            else None,
            expensive_areas=[
                (polygon_from_json(data=d["polygon"]), d["multiplier"])
                for d in data["expensive_areas"]
            ],
            valuable_areas=[
                (polygon_from_json(data=d["polygon"]), d["penalty"])
                for d in data["valuable_areas"]
            ],
            distance_cost=data["touring_costs"]["distance"],
            turn_cost=data["touring_costs"]["turn"],
            tool_radius=data["tool_radius"],
        )
