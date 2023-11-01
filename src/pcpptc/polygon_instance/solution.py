import json
import typing

from shapely.geometry import LineString, Point, Polygon

from ..utils import turn_angle


class Solution:
    def __init__(self, points, meta: typing.Optional[dict] = None):
        self.waypoints = [self._convert(p) for p in points]
        # the list of waypoints should not be closed manually
        if self.waypoints and self.waypoints[0] == self.waypoints[-1]:
            self.waypoints = self.waypoints[:-1]
        self.meta = meta if meta else {}

    def _convert(self, p) -> Point:
        try:
            return Point(p.x, p.y)
        except AttributeError as ae:
            return Point(p[0], p[1])

    def __iter__(self) -> typing.Iterable[Point]:
        yield from self.waypoints

    def __getitem__(self, item) -> typing.Union[Point, typing.List[Point]]:
        if not self.waypoints:
            msg = "Empty cycle."
            raise KeyError(msg)
        if type(item) is int:
            return self.waypoints[item % len(self.waypoints)]
        elif type(item) is slice:
            item: slice
            start = item.start % len(self.waypoints) if item.start else item.start
            stop = item.stop % len(self.waypoints) if item.stop else item.stop
            return self.waypoints[start : stop : item.step]
        msg = f"Unknown index {type(item)}."
        raise KeyError(msg)

    def __add__(self, other) -> typing.List[Point]:
        return list(self) + list(other)

    def __len__(self) -> int:
        return len(self.waypoints)

    def euclidean_length(self) -> float:
        l = 0.0
        for i in range(len(self)):
            l += self[i].distance(self[i + 1])
        return l

    def turn_angle_sum(self) -> float:
        angle_sum = 0.0
        for i in range(len(self)):
            angle_sum += turn_angle(self[i - 1], self[i], self[i + 1])
        return angle_sum

    def coverage_polygon(self, tool_radius: float) -> typing.Optional[Polygon]:
        if not self.waypoints:
            return None
        line = LineString([*self.waypoints, self.waypoints[0]])
        covering_polygon = line.buffer(
            tool_radius,
            cap_style=1,
            join_style=1,
        )
        return covering_polygon

    def to_json(
        self, file_path: typing.Optional[str] = None, as_string: bool = True
    ) -> typing.Union[str, dict]:
        data = {"waypoints": [[p.x, p.y] for p in self.waypoints], "meta": self.meta}
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
        if file_path:
            with open(file_path) as f:
                data = json.load(f)
        elif data_string:
            data = json.loads(data_string)
        return Solution(
            data["waypoints"], meta=data["meta"] if "meta" in data else None
        )
