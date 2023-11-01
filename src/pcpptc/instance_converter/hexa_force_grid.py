import math
import random

from ..grid_solver.grid_instance import (
    MultipliedTouringCosts,
    PointBasedInstance,
)
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
from ..instance_converter.grid import SimpleHexagonalGrid
from ..instance_converter.grid.boundary import BoundaryGrid
from ..instance_converter.grid.density_filter import DensityFilter
from ..instance_converter.grid_rating import GridRating
from ..instance_converter.interface import PolygonToGridGraphCoveringConverter
from ..instance_converter.polygonal_area import PolygonalArea
from ..polygon_instance import PolygonInstance
from ..utils import Point

_POINT_BASED_D = 3 / math.sqrt(3)
_EDGE_BASED_D = 4 / math.sqrt(3)


class HexaForceGrid(PolygonToGridGraphCoveringConverter):
    def __init__(
        self, full_coverage: bool = False, point_based: bool = False, show=True
    ):
        super().__init__(full_coverage=full_coverage)
        self.point_based = point_based
        self.show = show

    def _get_interior_grid(self, pi: PolygonInstance):
        f = _POINT_BASED_D if self.point_based else _EDGE_BASED_D
        gridder = SimpleHexagonalGrid(distance_factor=f)
        pe = PolygonalArea(polygon=pi.feasible_area)

        def random_grid():
            angle = random.random() * math.pi
            tranlation = (
                random.random() * 2 * pi.tool_radius,
                random.random() * 2 * pi.tool_radius,
            )
            grid_points = gridder(pi, angle=angle, translation=tranlation)
            return create_delaunay_graph(
                grid_points, length_limit=1.5 * f * pi.tool_radius, polygon=pe
            )

        gr = GridRating(pi)
        return list(max((random_grid() for i in range(20)), key=gr).nodes)

    def _get_boundary_points(self, pi: PolygonInstance, grid_dist: float):
        bg = BoundaryGrid(distance_factor=grid_dist, reduction_factor=0.1 * grid_dist)
        points = list(bg(pi))
        random.shuffle(points)
        df = DensityFilter(min_distance=0.5 * grid_dist)
        return list(df(points))

    def _determine_grid_distance(self, pi: PolygonInstance):
        f = _POINT_BASED_D if self.point_based else _EDGE_BASED_D
        grid_dist = pi.tool_radius * f
        return grid_dist

    def _run_olfati_saber(self, instance: PolygonInstance, points):
        d = (2 / math.sqrt(3)) * 2 * instance.tool_radius
        sim = ParticleSimulation(segment_width=0.1 * d)
        sim.add_polygon([(b[0], b[1]) for b in instance.feasible_area.exterior.coords])
        for hole in instance.feasible_area.interiors:
            sim.add_polygon([(b[0], b[1]) for b in hole.coords])
        for p in points:
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

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        grid_dist = self._determine_grid_distance(pi)
        interior_grid = self._get_interior_grid(pi)
        boundary_points = list(self._get_boundary_points(pi, grid_dist))
        points = interior_grid + boundary_points
        for _i in range(3):
            self._run_olfati_saber(pi, points)
            df = DensityFilter(
                min_distance=0.25 * pi.tool_radius,
                max_neighbors=6,
                radius=grid_dist * 1.1,
            )
            print(len(points), "before filtering")
            points = list(df(points))
            print(len(points), "after filtering")

        pe = PolygonalArea(polygon=pi.feasible_area)

        G = create_delaunay_graph(
            points, length_limit=1.5 * grid_dist * pi.tool_radius, polygon=pe
        )
        G = select_largest_component(G)
        attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = self._get_coverage_necessities(G, pi)
        return PointBasedInstance(G, obj, coverage_necessities)

    def get_recommended_orientation_number(self) -> int:
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return "HexaForceGridEpxerimental"
