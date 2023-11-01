import typing
import unittest
from math import *

from shapely.geometry import Point


def turn_angle(v0: Point, v1: Point, v2: Point) -> float:
    """
    Returns the turn angle moving from v0 to v2 over v1.
    """
    ta = pi - min_angle(v0, v2, origin=v1)
    assert 0 <= ta <= pi
    return ta


class TestTurnAngle(unittest.TestCase):
    def test_90deg(self):
        p0 = Point(1.0, 0.0)
        p1 = Point(0.0, 0.0)
        p2 = Point(0.0, 1.0)
        self.assertAlmostEqual(turn_angle(p0, p1, p2), 0.5 * pi, 2)

    def test_90deg_shifted(self):
        def add(a, b):
            return Point(a.x + b.x, a.y + b.y)

        s = Point(0.3, 0.4)
        p0 = add(Point(3.0, 0.0), s)
        p1 = add(Point(0.0, 0.0), s)
        p2 = add(Point(0.0, 1.0), s)
        self.assertAlmostEqual(turn_angle(p0, p1, p2), 0.5 * pi, 2)


def direction(v0: Point, origin: typing.Optional[Point] = None) -> float:
    if origin:
        v0 = Point(v0.x - origin.x, v0.y - origin.y)
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
