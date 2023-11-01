import math
import typing

import numpy as np
from pymunk import Vec2d

from .particle_simulation import Force, Particle
from .particle_simulation.neighborhood import Neighborhood


class OlfatiSaberForce(Force):
    def __init__(
        self,
        l: float,
        r: typing.Optional[float] = None,
        magnification=1.0,
        eps: float = 1.0,
        a=1.0,
        b=1.0,
        h=0.05,
    ):
        self.magnification = magnification
        self.l = l
        self.eps = eps
        self.a = a
        self.b = b
        self.c = abs(a - b) / math.sqrt(4 * a * b)
        self.h = h
        if r:
            self.r = r
        else:
            self.r = 1.2 * l
        self.r_normed = self.special_norm(self.r)
        self.l_normed = self.special_norm(l)

    def special_norm(self, z):
        z = np.array(z)
        return (1 / self.eps) * (math.sqrt(1 + self.eps * np.linalg.norm(z)) - 1)

    def rho(self, x):
        if x < self.h:
            return 1
        elif x <= 1:
            return 0.5 * (1 + math.cos(math.pi * ((x - self.h) / (1 - self.h))))
        else:
            return 0.0

    def phi_a(self, x: float):
        return self.rho(x / self.r_normed) * self.phi(x - self.l_normed)

    def phi(self, x: float) -> float:
        return 0.5 * (
            (self.a + self.b) * ((x + self.c) / math.sqrt(1 + (x + self.c) ** 2))
            + (self.a - self.b)
        )

    def mu(self, v: Vec2d):
        v = np.array(v)
        return v / math.sqrt(1 + self.eps * (np.sum(v**2)))

    def calculate(self, particle: Particle, neighborhood: Neighborhood) -> Vec2d:
        f = np.array([0.0, 0.0])
        nbr_force = np.array([0.0, 0.0])
        nbrs = [n for n in neighborhood.query(particle.position, self.r) if n != self]
        for n in nbrs:
            relative_pos = n.position - particle.position
            f += self.phi_a(self.special_norm(relative_pos)) * self.mu(relative_pos)
            nbr_force += np.array(n._last_force)
        if nbrs:
            nbr_force /= len(nbrs)
        return self.magnification * Vec2d(
            0.7 * f[0] + 0.3 * nbr_force[0], 0.7 * f[1] + 0.3 * nbr_force[1]
        )
