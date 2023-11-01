import math
import unittest

from .point import PointVertex


class VertexPassage:
    """
    A vertex passage is a basic solution element that describes the passage through
    a vertex v with the endpoints end_a and end_b. This can be a straight passage if
    all three waypoints are collinear. It can also be a U-turn if end_a==end_b.
    """

    def __init__(self, v: PointVertex, end_a: PointVertex, end_b: PointVertex):
        """
        v, end_a, end_b need to be waypoints with x and y, __hash__, and __lt__.
        """
        self.v = v
        self.end_a = min(end_a, end_b)
        if v in (end_a, end_b):
            msg = "center vertex cannot coincide with endpoints"
            raise ValueError(msg)
        self.end_b = max(end_a, end_b)

    def __hash__(self):
        return hash((hash(self.v), hash(self.end_a), hash(self.end_b)))

    def endpoints(self) -> tuple:
        """
        The endpoints of the passage. If it only contains one element, it is a u-turn.
        Contains between 1 and 2 elements.
        """
        return (self.end_a, self.end_b)

    def is_uturn(self) -> bool:
        return self.end_a == self.end_b

    def __eq__(self, other) -> bool:
        return self.v == other.v and self.endpoints() == other.endpoints()

    def __str__(self) -> str:
        return f"VertexPassage({self.end_a}<- {self.v} ->{self.end_b})"

    def turn_angle(self) -> float:
        """
        The turn angle of the vertex passed. It is pi for a u-turn. Otherwise, it is
        between 0 and pi. 0 means that the two endpoints are on opposing sides of v, i.target.,
        v can be passed straight.
        """
        u_ = self.end_a.point - self.v.point
        w_ = self.end_b.point - self.v.point
        u_a = math.atan2(u_.y, u_.x) % (2 * math.pi)
        w_a = math.atan2(w_.y, w_.x) % (2 * math.pi)
        assert 0 <= u_a <= 2 * math.pi
        assert 0 <= w_a <= 2 * math.pi
        angle = min((u_a - w_a) % (2 * math.pi), (w_a - u_a) % (2 * math.pi))
        assert 0 <= angle <= math.pi
        ta = math.pi - angle
        assert 0 <= ta <= math.pi, "Turn angle should always be between 0 and pi."
        return ta

    def __eucl_dist(self, a, b) -> float:
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def distance(self) -> float:
        """
        The distance of the passing. Starts at the endpoints. For computing the touring_costs,
        you have to divide it by 2. Otherwise your are counting each edge twice.
        """
        return self.__eucl_dist(self.v.point, self.end_a.point) + self.__eucl_dist(
            self.v.point, self.end_b.point
        )

    def __repr__(self) -> str:
        return str(self)


class TestVertexPassage(unittest.TestCase):
    def test_angle(self):
        P = PointVertex
        self.assertAlmostEqual(
            VertexPassage(
                v=P(1.0, 0.0), end_a=P(0.0, 0.0), end_b=P(2.0, 0.0)
            ).turn_angle(),
            0.0,
            2,
        )
        self.assertAlmostEqual(
            VertexPassage(
                v=P(1.0, 0.0), end_a=P(0.0, 0.0), end_b=P(1.0, 1.0)
            ).turn_angle(),
            0.5 * math.pi,
            2,
        )
        self.assertAlmostEqual(
            VertexPassage(
                v=P(1.0, 0.0), end_a=P(0.0, 0.0), end_b=P(0.0, 0.0)
            ).turn_angle(),
            math.pi,
            2,
        )
        self.assertAlmostEqual(
            VertexPassage(
                v=P(0.0, 0.0), end_a=P(1.0, 0.0), end_b=P(1.0, 1.0)
            ).turn_angle(),
            0.75 * math.pi,
            2,
        )
        self.assertAlmostEqual(
            VertexPassage(
                v=P(0.0, 0.0), end_a=P(-1.0, 0.0), end_b=P(1.0, 1.0)
            ).turn_angle(),
            0.25 * math.pi,
            2,
        )
