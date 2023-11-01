import math
import typing
import unittest
from math import *

from .point import Point


def _free_turn_angle(v0, v1, v2) -> float:
    """
    Returns the turn angle moving from v0 to v2 over v1.
    """
    ta = pi - min_angle(v0, v2, origin=v1)
    assert 0 <= ta <= pi
    return ta


def _forced_turn_angle(
    v0, v1, v2, forced_orientation_at_v1: typing.Optional[float]
) -> float:
    headings = [direction(v0, origin=v1), direction(v2, origin=v1)]
    o = forced_orientation_at_v1
    return min(
        abs_angle_difference(headings[0], o)
        + abs_angle_difference(headings[1], o + math.pi),
        abs_angle_difference(headings[1], o)
        + abs_angle_difference(headings[0], o + math.pi),
    )


def turn_angle(
    v0, v1, v2, forced_orientation_at_v1: typing.Optional[float] = None
) -> float:
    """
    Returns the turn angle moving from v0 to v2 over v1.
    """
    if forced_orientation_at_v1 is None:
        return _free_turn_angle(v0, v1, v2)
    else:
        return _forced_turn_angle(v0, v1, v2, forced_orientation_at_v1)


class TestTurnAngle(unittest.TestCase):
    def test_90deg(self):
        p0 = Point(1.0, 0.0)
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0, 1.0)
        self.assertAlmostEqual(turn_angle(p0, p1, p2), 0.5 * pi, 2)

    def test_90deg_shifted(self):
        s = Point(0.3, 0.4)
        p0 = (Point(1.0, 0.0) * 3) + s
        p1 = Point(0.0, 0.0) + s
        p2 = Point(0.0, 1.0) + s
        self.assertAlmostEqual(turn_angle(p0, p1, p2), 0.5 * pi, 2)


def direction(v0: Point, origin: typing.Optional[Point] = None) -> float:
    v0 = Point(v0)
    if origin:
        origin = Point(origin)
        v0 = v0 - origin
    return atan2(v0.y, v0.x) % (2 * pi)


class TestDirection(unittest.TestCase):
    def test_0deg(self):
        self.assertAlmostEqual(direction(Point(1.0, 0.0)), 0.0 * pi, 2)

    def test_90deg(self):
        self.assertAlmostEqual(direction(Point(0.0, 1.0)), 0.5 * pi, 2)

    def test_180deg(self):
        self.assertAlmostEqual(direction(Point(-1.0, 0.0)), pi, 2)

    def test_270deg(self):
        self.assertAlmostEqual(direction(Point(0.0, -1.0)), 1.5 * pi, 2)


def abs_angle_difference(a0, a1):
    return min((a0 - a1) % (2 * pi), (a1 - a0) % (2 * pi))


class TestAbsAngleDifference(unittest.TestCase):
    def test_0deg(self):
        self.assertAlmostEqual(abs_angle_difference(0.5 * pi, 0.5 * pi), 0.0, 2)

    def test_90deg(self):
        self.assertAlmostEqual(abs_angle_difference(1.0 * pi, 0.5 * pi), 0.5 * pi, 2)

    def test_90deg2(self):
        self.assertAlmostEqual(abs_angle_difference(1.75 * pi, 0.25 * pi), 0.5 * pi, 2)

    def test_180deg(self):
        self.assertAlmostEqual(abs_angle_difference(1.5 * pi, 0.5 * pi), 1.0 * pi, 2)


def clockwise_angle(v0, v1, origin=None) -> float:
    """
    Returns the clockwise angle from v0 to v1
    """
    a0 = direction(v0, origin=origin)
    a1 = direction(v1, origin=origin)
    assert 0 <= a0 <= 2 * pi
    assert 0 <= a1 <= 2 * pi
    return (a0 - a1) % (2 * pi)


class TestClockwiseAngle(unittest.TestCase):
    def test_90deg(self):
        p0 = Point(0.0, 1.0)
        p1 = Point(1.0, 0.0)
        self.assertAlmostEqual(
            clockwise_angle(p0, p1, origin=Point(0.0, 0.0)), 0.5 * pi, 2
        )

    def test_270deg(self):
        p0 = Point(1.0, 0.0)
        p1 = Point(0.0, 1.0)
        self.assertAlmostEqual(
            clockwise_angle(p0, p1, origin=Point(0.0, 0.0)), 1.5 * pi, 2
        )


def min_angle(v0, v1, origin=None) -> float:
    """
    Returns the minimum angle between two vectors (or a triple of waypoints)
    """
    ma = min(clockwise_angle(v0, v1, origin), clockwise_angle(v1, v0, origin))
    assert 0 <= ma <= pi
    return ma


class TestMinAngle(unittest.TestCase):
    def test_90deg(self):
        p0 = Point(0.0, 1.0)
        p1 = Point(1.0, 0.0)
        self.assertAlmostEqual(min_angle(p0, p1, origin=Point(0.0, 0.0)), 0.5 * pi, 2)

    def test_270deg(self):
        p0 = Point(1.0, 0.0)
        p1 = Point(0.0, 1.0)
        self.assertAlmostEqual(min_angle(p0, p1, origin=Point(0.0, 0.0)), 0.5 * pi, 2)
