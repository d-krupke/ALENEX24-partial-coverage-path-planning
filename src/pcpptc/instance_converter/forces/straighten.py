import typing

from pymunk import Vec2d

from .particle_simulation import Force, Particle
from .particle_simulation.neighborhood import Neighborhood


class Straighten(Force):
    def __init__(
        self,
        pairs: typing.Dict[typing.Tuple[Particle, Particle], float],
        multiplier=1.0,
    ):
        self.multiplier = multiplier
        self.pairs = pairs

    def calculate(self, particle: Particle, neighborhood: Neighborhood) -> Vec2d:
        f = Vec2d(0.0, 0.0)
        for pair, strength in self.pairs.items():
            c = 0.5 * (pair[0].position + pair[1].position)
            d = c - particle.position
            f += strength * d
        return self.multiplier * f
