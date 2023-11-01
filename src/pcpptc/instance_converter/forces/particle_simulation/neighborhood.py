import typing

import numpy as np
import scipy.spatial
from pymunk import Vec2d

from .particle import Particle


class Neighborhood:
    """
    A neighborhood that can be used for force computation. It is handed over to the
    Force-object on every loop.
    """

    def __init__(self, particles: typing.List[Particle]):
        self._particles = list(particles)
        self._positions = np.array([[p.position[0], p.position[1]] for p in particles])
        self._kdtree = scipy.spatial.KDTree(self._positions)

    def query(self, position: Vec2d, r: float):
        """
        Query the particles within range `reptition_of_each_orientation` around `position`.
        """
        q = self._kdtree.query_ball_point(r=r, x=position)
        return [self._particles[p] for p in q]
