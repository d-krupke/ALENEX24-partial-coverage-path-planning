import math
import typing

from forces.particle_simulation import ParticleSimulation, ParticleWithForce
from forces.repulsion import Repulsion

from pcpptc.grid_solver.grid_instance import Point, PointVertex
from pcpptc.polygon_instance import PolygonInstance


def expand(instance: PolygonInstance, grid_points: typing.List[PointVertex]):
    r = (2 / math.sqrt(3)) * 2 * instance.tool_radius
    sim = ParticleSimulation(segment_width=instance.tool_radius * 0.1)
    sim.add_polygon([(b[0], b[1]) for b in instance.feasible_area.exterior.coords])
    for hole in instance.feasible_area.interiors:
        sim.add_polygon([(b[0], b[1]) for b in hole.coords])
    for p in grid_points:
        particle = ParticleWithForce((p[0], p[1]), radius=0.1)
        particle.info["vertex"] = p
        particle.add_force(
            Repulsion(r, multiplier=200, strength=lambda d: 1 / (d**3))
        )
        sim.add_particle(particle)
    sim.loop(20, dt=0.1)
    for particle in sim.particles:
        vp = particle.info["vertex"]
        pos = particle.position
        vp.point = Point(pos)
