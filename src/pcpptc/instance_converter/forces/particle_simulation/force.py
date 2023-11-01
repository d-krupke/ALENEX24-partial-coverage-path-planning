from abc import ABC, abstractmethod

from pymunk import Vec2d

from .neighborhood import Neighborhood
from .particle import Particle


class Force(ABC):
    """
    For implementing a force for ParticleWithForce.
    """

    @abstractmethod
    def calculate(self, particle: Particle, neighborhood: Neighborhood) -> Vec2d:
        """
        Calculates a force (with particle position as origin. Same orientation as the
        world coordinate system.
        The neighborhood can be used to query nearby other particles efficiently.
        """
        raise NotImplementedError()


class ParticleWithForce(Particle):
    """
    This particle is used to simulate the forces.
    Use add_force to add a force. You can query the last force using `force()`.
    """

    def __init__(
        self, position, radius=10, friction=1.0, elasticity=0.1, impulse_limit=10.0
    ):
        super().__init__(position, radius, friction, elasticity)
        self.impulse_limit = impulse_limit
        self._forces = []
        self._last_force = Vec2d(0.0, 0.0)

    def add_force(self, force: Force):
        """
        Add a force to the particle.
        """
        self._forces.append(force)

    def loop(self, neighborhood: Neighborhood):
        """
        For internal use.
        """
        force_sum = Vec2d(0.0, 0.0)
        for fc in self._forces:
            f = fc.calculate(self, neighborhood)
            force_sum += f
        if force_sum.get_length_sqrd() > self.impulse_limit**2:
            force_sum *= (self.impulse_limit**2) / force_sum.get_length_sqrd()
        self.apply_impulse(force_sum)
