import typing

import pymunk
from pymunk import Segment, Vec2d

from .force import ParticleWithForce
from .neighborhood import Neighborhood


class ParticleSimulation:
    """
    The actual simulation. It hands all over the the physics engine pymunk which does the
    actual work. Note that the right distances are important for proper function.
    Too small values seem to become inaccurate. Use the transformers to easily scale.
    You can add polygons and segments as obstacles.
    You can also directly use the visualization.
    The two most important functions are `add_polygon` and `add_particle`.
    Best keep the default values for all parameter and try to scale instead.

    You implement your logic as forces that you add to the particles directly.
    """

    def __init__(
        self,
        damping=0.1,
        segment_elasticity=0.1,
        segment_friction=1.0,
        segment_width=2.0,
    ):
        self.particles = []
        self._space = pymunk.Space()
        self._space.damping = damping
        self._segment_elasticity = segment_elasticity
        self._segment_friction = segment_friction
        self.segments = []
        self._segment_width = segment_width

    def add_polygon(self, polygon: typing.List[Vec2d]):
        """
        Adds a polygon. The particles cannot enter or leave it (most of the time. With
        bad values, it becomes inaccurate).
        """
        for i in range(len(polygon)):
            p0 = polygon[i % len(polygon)]
            p1 = polygon[(i + 1) % len(polygon)]
            self.add_segment(p0, p1)

    def add_segment(self, start: Vec2d, end: Vec2d):
        """
        Adds a segment obstacle.
        """
        seg = pymunk.Segment(self._space.static_body, start, end, self._segment_width)
        seg.elasticity = self._segment_elasticity
        seg.friction = self._segment_friction
        self._space.add(seg)
        self.segments.append(seg)
        return seg

    def get_bounding_box(self) -> typing.Tuple[Vec2d, Vec2d]:
        """
        Returns the bounding box of the simulation.
        """

        def iter_coordinates():
            for s in self.segments:
                s: Segment
                yield s.a
                yield s.b
            for p in self.particles:
                yield p.position

        bb = [
            Vec2d(
                m(p[0] for p in iter_coordinates()), m(p[1] for p in iter_coordinates())
            )
            for m in [min, max]
        ]
        return bb[0], bb[1]

    def remove_segment(self, segment):
        """
        Removes a seement again.
        """
        self.segments.remove(segment)
        self._space.remove(segment)

    def add_particle(self, particle: ParticleWithForce):
        """
        Adds are particle that has forces.
        """
        if particle in self.particles:
            msg = "Already contained."
            raise ValueError(msg)
        self._space.add(particle._body, particle._circle)
        self.particles.append(particle)

    def remove_particle(self, particle: ParticleWithForce):
        """
        Removes a particle again.
        """
        self.particles.remove(particle)
        self._space.remove(particle._body, particle._circle)

    def loop(self, n=1, dt=0.01):
        """
        Does n simulation steps.
        """
        for _i in range(n):
            self.step(dt)

    def step(self, dt=0.01):
        """
        Does one simulation step with a time delta of dt.
        """
        self._space.step(dt)
        neighborhood = Neighborhood(self.particles)
        for particle in self.particles:
            particle.loop(neighborhood)
