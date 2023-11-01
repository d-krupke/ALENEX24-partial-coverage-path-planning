import typing

import numpy as np
from particle_simulation import Force, Particle
from particle_simulation.neighborhood import Neighborhood
from pymunk import Vec2d

from pcpptc.utils import distance


def inv_squared(d: float) -> float:
    return 1 / (d**2)


class Repulsion(Force):
    def calculate(self, particle: Particle, neighborhood: Neighborhood) -> Vec2d:
        p = particle
        nearby = neighborhood.query(particle.position, self.range)
        f = np.array([0.0, 0.0])
        for n in nearby:
            if n == particle:
                continue
            strength = self.multiplier * self.strength(
                distance(particle.position, n.position)
            )
            v = np.array([p.position[i] for i in [0, 1]]) - np.array(
                [n.position[i] for i in [0, 1]]
            )
            f += strength * v
        return Vec2d(f[0], f[1])

    def __init__(
        self,
        r: float,
        multiplier=1.0,
        strength: typing.Callable[[float], float] = inv_squared,
    ):
        self.range = r
        self.strength = strength
        self.multiplier = multiplier
