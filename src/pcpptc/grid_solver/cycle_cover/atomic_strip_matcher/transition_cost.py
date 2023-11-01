import math
import unittest

from pcpptc.utils import abs_angle_difference, direction

from ...grid_instance import PointVertex, SimpleTouringCosts, TouringCosts
from .atomic_strip_vertex import AtomicStripVertex


class TransitionCostCalculator:
    def __init__(self, touring_cost: TouringCosts):
        self.touring_cost = touring_cost

    def __call__(self, v0: AtomicStripVertex, v1: AtomicStripVertex):
        distance_cost = self.touring_cost.distance_cost_of_edge(
            v0.point_vertex, v1.point_vertex
        )
        first_turn = abs_angle_difference(
            v0.direction, direction(v1.point_vertex.point, origin=v0.point_vertex.point)
        )
        second_turn = abs_angle_difference(
            direction(v1.point_vertex.point, origin=v0.point_vertex.point),
            (v1.direction + math.pi) % (2 * math.pi),
        )
        turn_cost = self.touring_cost.turn_cost_at_vertex(
            at=v0.point_vertex, angle=first_turn
        ) + self.touring_cost.turn_cost_at_vertex(at=v1.point_vertex, angle=second_turn)
        return turn_cost + distance_cost


class TransitionCostCalculatorTest(unittest.TestCase):
    def test_dist(self):
        c = TransitionCostCalculator(SimpleTouringCosts(0.0, 1.0))
        v0 = AtomicStripVertex(0, PointVertex(1.0, 1.0), 1.0)
        v1 = AtomicStripVertex(1, PointVertex(1.0, 3.0), 1.0)
        self.assertAlmostEqual(c(v0, v1), 2.0, 2)

    def test_90deg(self):
        c = TransitionCostCalculator(SimpleTouringCosts(1.0, 0.0))
        v0 = AtomicStripVertex(0, PointVertex(1.0, 1.0), 0.0)
        v1 = AtomicStripVertex(1, PointVertex(1.0, 3.0), 1.5 * math.pi)
        self.assertAlmostEqual(c(v0, v1), 0.5 * math.pi, 2)

    def test_180deg(self):
        c = TransitionCostCalculator(SimpleTouringCosts(1.0, 0.0))
        v0 = AtomicStripVertex(0, PointVertex(1.0, 1.0), 0.0)
        v1 = AtomicStripVertex(1, PointVertex(-1.0, 1.0), 0.0)
        self.assertAlmostEqual(c(v0, v1), math.pi, 2)

    def test_360deg(self):
        c = TransitionCostCalculator(SimpleTouringCosts(1.0, 0.0))
        v0 = AtomicStripVertex(0, PointVertex(1.0, 1.0), 0.0)
        v1 = AtomicStripVertex(1, PointVertex(-1.0, 1.0), math.pi)
        self.assertAlmostEqual(c(v0, v1), 2 * math.pi, 2)
