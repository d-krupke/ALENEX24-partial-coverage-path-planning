import pymunk


class Particle:
    """
    A simple base class for a particle. Is inherited by ParticleWithForce to prevent
    cyclic dependencies.
    """

    def __init__(self, position, radius=10, friction=1.0, elasticity=0.1):
        self._body = pymunk.Body(mass=1, moment=10)
        self._body.position = (position[0], position[1])
        self._circle = pymunk.Circle(self._body, radius=radius)
        self._circle.elasticity = elasticity
        self._circle.friction = friction
        self.info = {}

    @property
    def position(self):
        return self._body.position

    def apply_force(self, force):
        self._body.apply_force_at_world_point(force, self._body.position)
        return self._body.force

    def apply_impulse(self, impulse):
        self._body.apply_force_at_world_point(impulse, self._body.position)
        return self._body.force

    @property
    def force(self):
        return self._body.force

    @property
    def x(self):
        return self._body.position.x

    @property
    def y(self):
        return self._body.position.y
