# %%
import math
import typing

from shapely.geometry import LinearRing, Polygon

from ..grid_solver.cycle_connecting import connect_cycles_via_pcst
from ..grid_solver.grid_instance import (
    CoverageNecessities,
    MultipliedTouringCosts,
    PointBasedInstance,
    PointVertex,
    SimpleCoverage,
)
from ..instance_converter import RotatingRegularHexagonal
from ..instance_converter.forces.olfati_saber_force import OlfatiSaberForce
from ..instance_converter.forces.particle_simulation import (
    ParticleSimulation,
    ParticleWithForce,
)
from ..instance_converter.graph import (
    attach_multiplier_to_graph,
    create_delaunay_graph,
    select_largest_component,
)
from ..instance_converter.grid.density_filter import DensityFilter
from ..instance_converter.grid.feasibility_filter import FeasibilityFilter
from ..instance_converter.polygonal_area import PolygonalArea
from ..polygon_instance import PolygonInstance, Solution

# %%
from ..solver_selection.abstract_solver import (
    PolygonInstanceSolver,
    convert_tour_to_list,
)
from ..utils import Point, distance

# grid_points = SimpleHexagonalGrid()(instance)

# %%


def _move_to_target(p: Point, target: Point, step_size: float):
    dist = distance(p, target)
    if dist < 2 * step_size:
        step_size = 0.5 * dist
    step = (target.to_np() - p.to_np()) / dist
    coord = p.to_np() + step_size * step
    return Point(coord[0], coord[1])


def _points_on_segment(
    begin: Point, end: Point, max_dist: float
) -> typing.Iterable[Point]:
    assert begin != end
    p = begin
    yield p
    while distance(p, end) > max_dist:
        p = _move_to_target(p, end, max_dist)
        yield p


def get_points_on_ring(boundary: LinearRing, max_dist: float):
    points = []
    for i, p in enumerate(boundary.coords):
        p0 = Point(p)
        p1 = Point(boundary.coords[(i + 1) % len(boundary.coords)])
        if p0 == p1:
            continue
        for p_ in _points_on_segment(p0, p1, max_dist):
            points.append(PointVertex(p_))
    return points


def boundaries(polygon: Polygon):
    yield polygon.exterior
    yield from polygon.interiors


def get_points_around_boundary(pi: PolygonInstance) -> typing.List[PointVertex]:
    slightly_reduced_boundary = pi.feasible_area.buffer(-0.03 * pi.tool_radius)
    points = []
    for p in boundaries(slightly_reduced_boundary):
        points += get_points_on_ring(p, 2 * pi.tool_radius)
    return points


class ExperimentalSolver(PolygonInstanceSolver):
    def __call__(self, instance: PolygonInstance):
        grid_points = list(RotatingRegularHexagonal()(instance).graph.nodes)
        df = DensityFilter(
            min_distance=instance.tool_radius,
            max_neighbors=6,
            radius=3 * instance.tool_radius,
        )
        boundary_points = list(df(get_points_around_boundary(instance)))

        grid_points += boundary_points

        # %%
        df = DensityFilter(
            min_distance=0.2 * instance.tool_radius,
            max_neighbors=6,
            radius=3 * instance.tool_radius,
        )
        ff = FeasibilityFilter(instance.feasible_area)
        grid_points = list(ff(df(grid_points)))
        # %%

        d = (2 / math.sqrt(3)) * 2 * instance.tool_radius
        sim = ParticleSimulation(segment_width=0.05 * instance.tool_radius)
        sim.add_polygon([(b[0], b[1]) for b in instance.feasible_area.exterior.coords])
        for hole in instance.feasible_area.interiors:
            sim.add_polygon([(b[0], b[1]) for b in hole.coords])
        for p in grid_points:
            particle = ParticleWithForce(
                (p[0], p[1]), radius=0.1 * instance.tool_radius
            )
            particle.info["vertex"] = p
            force = OlfatiSaberForce(l=d, magnification=50, eps=1, h=0.02)
            particle.add_force(force)
            sim.add_particle(particle)
        sim.loop(60)
        for particle in sim.particles:
            vp = particle.info["vertex"]
            pos = particle.position
            vp.point = Point(pos)

        # %%

        G = create_delaunay_graph(
            grid_points,
            length_limit=3 * instance.tool_radius,
            polygon=PolygonalArea(polygon=instance.feasible_area),
        )

        G = select_largest_component(G)
        attach_multiplier_to_graph(G, instance, 0.25 * instance.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=instance.distance_cost, turn_factor=instance.turn_cost
        )
        coverage_necessities = CoverageNecessities(SimpleCoverage())
        pbi = PointBasedInstance(G, obj, coverage_necessities)
        cc = CycleCoverSolver(k=3, r=2)(pbi)
        t = connect_cycles_via_pcst(pbi, cc)
        solution = Solution(convert_tour_to_list(t))
        return solution
