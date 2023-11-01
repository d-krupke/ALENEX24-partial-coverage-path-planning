"""
This package provides some utils like basic geometry functions.
Note that his code is a conglomerate of geometry functions and
there are, e.g., multiple Point classes used in this package.
This is necessary as some of the used packages require different
Point classes.
"""

from .angles import abs_angle_difference, direction, turn_angle
from .point import Point, distance

__all__ = ["Point", "distance", "turn_angle", "direction", "abs_angle_difference"]
