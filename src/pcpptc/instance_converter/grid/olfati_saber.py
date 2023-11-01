import math
import typing

from forces.olfati_saber_force import OlfatiSaberForce
from forces.particle_simulation import ParticleSimulation, ParticleWithForce
from grid_instance import Point, PointVertex
from optimizer.polygon_instance import PolygonInstance


def straighten_with_os(
    instance: PolygonInstance, grid_points: typing.List[PointVertex]
):
    d = (2 / math.sqrt(3)) * 2 * instance.tool_radius
    sim = ParticleSimulation(segment_width=0.05 * instance.tool_radius)
    sim.add_polygon([(b[0], b[1]) for b in instance.feasible_area.exterior.coords])
    for hole in instance.feasible_area.interiors:
        sim.add_polygon([(b[0], b[1]) for b in hole.coords])
    for p in grid_points:
        particle = ParticleWithForce((p[0], p[1]), radius=0.1 * instance.tool_radius)
        particle.info["vertex"] = p
        force = OlfatiSaberForce(l=d, magnification=50, eps=1, h=0.01)
        particle.add_force(force)
        sim.add_particle(particle)
    sim.loop(30, dt=0.1)
    for particle in sim.particles:
        vp = particle.info["vertex"]
        pos = particle.position
        vp.point = Point(pos)
