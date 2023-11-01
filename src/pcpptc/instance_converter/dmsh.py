import math
import typing

from shapely.geometry import Point, Polygon

from ..grid_solver import PointBasedInstance, PointVertex
from ..grid_solver.grid_instance import MultipliedTouringCosts
from ..instance_converter.graph import (
    attach_multiplier_to_graph,
    create_delaunay_graph,
    select_largest_component,
)
from ..instance_converter.grid_size import get_optimal_grid_edge_length
from ..instance_converter.interface import PolygonToGridGraphCoveringConverter
from ..instance_converter.polygonal_area import PolygonalArea
from ..polygon_instance import PolygonInstance

_POINT_BASED_DISTANCE = 3 / math.sqrt(3)
_EDGE_BASED_DISTANCE = 4 / math.sqrt(3)


def _largest_poly(poly):
    if type(poly) is Polygon:
        return poly
    else:
        polys = list(poly)
        areas = [p.area for p in polys]
        print(
            f"Result is a MultiPolygon of polygons with area {areas}. Selecting largest as workaround."
        )
        return max(poly, key=lambda p: p.area)


from shapely.geometry import Polygon

from ..utils.angles import min_angle


def _remove_duplicates(coords):
    prev = None
    for p in coords:
        if prev is None or prev != p:
            yield p
            prev = p


def _remove_spikes_from_coords(coords, r, f, s):
    coords = list(_remove_duplicates(coords))
    for i, p1 in enumerate(coords[:-1]):
        p0 = coords[i - 1] if i != 0 else coords[-2]
        p2 = coords[(i + 1) % len(coords)]
        angle = min_angle(p0, p2, origin=p1)
        if angle < s:
            print("Spike at", p0, p1, p2, "with angle", angle)
            p0 = np.array(p0)
            p1 = np.array(p1)
            p2 = np.array(p2)
            p0p1 = np.linalg.norm(p0 - p1)
            p2p1 = np.linalg.norm(p0 - p1)
            assert (
                p0p1 > f * r
            ), "Segment too short. Such short segments should have been removed before."
            assert (
                p2p1 > f * r
            ), "Segment too short. Such short segments should have been removed before."
            p0_ = p1 + f * (p0 - p1) / p0p1
            p2_ = p2 + f * (p2 - p1) / p2p1
            yield (p0_[0], p0_[1])
            yield (p2_[0], p2_[1])
        else:
            yield p1


def _fix_polygon_with_spikes(poly: Polygon, r, f=0.01, s=0.05):
    exterior = list(_remove_spikes_from_coords(poly.exterior.coords, r, f, s))
    holes = [
        list(_remove_spikes_from_coords(h.coords, r, f, s)) for h in poly.interiors
    ]
    return Polygon(exterior, holes=holes)


class DmshGrid(PolygonToGridGraphCoveringConverter):
    def to_dmsh_polygon(self, poly):
        import dmsh

        poly = Polygon(poly)
        poly: Polygon
        coords = poly.exterior.coords
        coords = list(coords)[:-1]
        assert len(coords) >= 3, "A polygon needs at least 3 coordinates"
        return dmsh.Polygon([[c[0], c[1]] for c in coords])

    def to_geo(self, pi: PolygonInstance):
        if self.hard_corners:
            poly = pi.original_area
            poly = poly.simplify(self.simplification * pi.tool_radius)
            poly = poly.buffer(-pi.tool_radius, cap_style=2, join_style=2)
            poly = _largest_poly(poly)
            poly = _fix_polygon_with_spikes(poly, r=pi.tool_radius)
        else:
            poly = pi.feasible_area
        poly = poly.buffer(-self.buffer * pi.tool_radius, cap_style=2, join_style=2)
        poly = poly.simplify(self.simplification * pi.tool_radius)
        poly = _largest_poly(poly)
        assert poly.is_valid, "Polygon should be valid after processing."
        geo = self.to_dmsh_polygon(poly.exterior)
        for hole in poly.interiors:
            geo = geo - self.to_dmsh_polygon(hole)
        return geo

    def __init__(
        self,
        full_coverage=False,
        point_based=False,
        buffer: float = 0.05,
        simplification=0.1,
        opt_method: str = "CVT-full",
        scale: float = 0.95,
        iterations: int = 1000,
        hard_corners: bool = False,
        dmsh_fallback: bool = False,
    ):
        super().__init__(full_coverage=full_coverage)
        self.hard_corners = hard_corners
        self.iterations = iterations
        self.scale = scale
        if buffer < 0.0:
            msg = "Buffer has to be positive."
            raise ValueError(msg)
        self.opt_method = opt_method
        self.buffer = buffer
        self.simplification = simplification
        self.point_based = point_based
        self.dmsh_fallback = dmsh_fallback
        self._d = _POINT_BASED_DISTANCE if point_based else _EDGE_BASED_DISTANCE

    def _mesh(self, pi: PolygonInstance) -> typing.List[PointVertex]:
        # dmsh and optimesh have changed to a commercial license and purged
        # the free version from the internet. This workaround will allow
        # to fall back in case the old free version is not installed.
        import dmsh
        import optimesh

        geo = self.to_geo(pi)
        d = self.scale * _EDGE_BASED_DISTANCE * pi.tool_radius
        X, cells = dmsh.generate(geo, target_edge_size=d, tol=1.0e-4)
        if np.isnan(X).any():
            msg = "NaN in returned dmsh coordinates."
            raise ValueError(msg)
        print("Optimize grid with", self.opt_method)
        X, cells = optimesh.optimize_points_cells(
            X, cells, self.opt_method, 1.0e-5, self.iterations
        )
        grid_points = [PointVertex(x[0], x[1]) for x in X]
        return grid_points

    def _fallback(self, pi: PolygonInstance) -> PointBasedInstance:
        print("Falling back to gmsh.")
        gmsh = GmshGrid(
            full_coverage=self.full_coverage,
            point_based=self.point_based,
            buffer=self.buffer,
            simplification=self.simplification,
            opt_method=self.opt_method,
            scale=self.scale,
            iterations=self.iterations,
            quad=False,
            alg=9,
            hard_corners=self.hard_corners,
            hole_workround=True,
        )
        return gmsh(pi)

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        try:
            grid_points = self._mesh(pi)
            pe = PolygonalArea(polygon=pi.feasible_area)
            G = create_delaunay_graph(
                grid_points, length_limit=3 * self._d * pi.tool_radius, polygon=pe
            )
            G = select_largest_component(G)
            attach_multiplier_to_graph(G, pi, 0.25 * pi.tool_radius)
            obj = MultipliedTouringCosts(
                G, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
            )
            coverage_necessities = self._get_coverage_necessities(G, pi)
            return PointBasedInstance(G, obj, coverage_necessities)
        except (
            AssertionError
        ) as ae:  # Fallback on some numeric issues because dmsh is not that stable.
            if (
                self.dmsh_fallback
                and str(ae) == "Exceeded maximum number of boundary steps."
            ):
                return self._fallback(pi)
            else:
                raise ae
        except ImportError as ie:
            print("dmsh not installed. Falling back to gmsh.")
            return self._fallback(pi)
        except ValueError as ve:
            return self._fallback(pi)

    def get_recommended_orientation_number(self) -> int:
        return 3

    def get_recommended_repetition_number(self) -> int:
        return 2

    def identifier(self) -> str:
        return (
            f"DmshGrid(full_coverage={self.full_coverage},"
            f" point_based={self.point_based}, opt={self.opt_method},"
            f" scale={self.scale}, buffer={self.buffer}, "
            f"simplification={self.simplification}, iterations={self.iterations},"
            f" hard_corners={self.hard_corners})"
        )


import networkx as nx
import numpy as np
import pygmsh


class GmshGrid(PolygonToGridGraphCoveringConverter):
    def to_coords(self, poly, expand=None):
        poly = Polygon(poly)
        poly: Polygon
        coords = poly.exterior.coords
        if expand and self.hole_workaround:
            coords = self._expand_coords(list(coords), expand)
        coords = list(coords)[:-1]
        return coords

    def _expand_coords(self, coords: list, d: float):
        """
        Replaces long edges by shorter one (roughly d) because some grid algorithms
        strugle with holes and make the edges too long.
        """
        for p0, p1 in zip(coords[:-1], coords[1:]):
            dist = Point(p0).distance(Point(p1))
            steps = round(dist / d)
            if steps <= 1:
                yield p0
            else:
                step_length = dist / steps
                v = step_length * ((np.array(p1) - np.array(p0)) / dist)
                p = np.array(p0)
                for _i in range(steps):
                    yield (p[0], p[1])
                    p += v
        yield coords[-1]

    def to_geo(self, pi: PolygonInstance):
        if self.hard_corners:
            poly = pi.original_area
            poly = poly.simplify(self.simplification * pi.tool_radius)
            poly = poly.buffer(-pi.tool_radius, cap_style=2, join_style=2)
            poly = _largest_poly(poly)
            poly = _fix_polygon_with_spikes(poly, r=pi.tool_radius)
        else:
            poly = pi.feasible_area
        poly = poly.buffer(-self.buffer * pi.tool_radius)
        poly = poly.simplify(self.simplification * pi.tool_radius)
        poly = _largest_poly(poly)
        with pygmsh.geo.Geometry() as geom:
            d = self.scale * get_optimal_grid_edge_length(
                not self.quad, pi.tool_radius, self.point_based
            )
            holes = [
                geom.add_polygon(self.to_coords(hole, d), make_surface=False)
                for hole in poly.interiors
            ]
            poly = geom.add_polygon(
                self.to_coords(poly.exterior), holes=holes, mesh_size=d
            )
            if self.quad:
                geom.set_recombined_surfaces([poly.surface])
            if self.alg:
                mesh = geom.generate_mesh(dim=2, algorithm=self.alg)
            else:
                mesh = geom.generate_mesh(dim=2)
        return mesh

    def mesh_to_graph(self, points, cell_data):
        points = [PointVertex(p) for p in points]
        graph = nx.Graph()
        graph.add_nodes_from(points)
        for triangle in cell_data:
            for i, idx in enumerate(triangle):
                graph.add_edge(points[idx], points[triangle[(i + 1) % len(triangle)]])
        return graph

    algs = {
        1: "MeshAdapt",
        2: "Automatic",
        3: "Initial mesh only",
        5: "Delaunay",
        6: "Frontal-Delaunay",
        7: "BAMG",
        8: "Frontal-Delaunay for Quads",
        9: "Packing of Parallelograms",
    }

    def __init__(
        self,
        full_coverage=False,
        point_based=False,
        buffer: float = 0.05,
        simplification=0.1,
        opt_method: str = "CVT-full",
        scale: float = 1.0,
        iterations: int = 1000,
        quad=False,
        alg=9,
        hard_corners: bool = False,
        hole_workround: bool = True,
    ):
        super().__init__(full_coverage=full_coverage)
        print("using gmesh with", self.algs.get(alg, "undefined"))
        print("Good options are 1, 4, and 9.")
        self.hard_corners = hard_corners
        self.iterations = iterations
        self.quad = quad
        self.scale = scale
        self.alg = alg
        if buffer < 0.0:
            msg = "Buffer has to be positive."
            raise ValueError(msg)
        self.opt_method = opt_method
        self.buffer = buffer
        self.simplification = simplification
        self.point_based = point_based
        self.hole_workaround = hole_workround

    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        mesh = self.to_geo(pi)
        if self.quad:
            X = mesh.points
            data = []
            for d in mesh.cells:
                if d.type in ["triangle", "quad", "line"]:
                    for e in d.data:
                        data.append(e)
            graph = self.mesh_to_graph(X, data)
        else:
            X, cells = mesh.points, mesh.cells[1].data.astype(int)
            if self.opt_method and not self.quad:
                print("Optimize grid with", self.opt_method)
                try:
                    import optimesh

                    X, cells = optimesh.optimize_points_cells(
                        X, cells, self.opt_method, 1.0e-5, self.iterations
                    )
                except ImportError as ie:
                    print("==========================================================")
                    print("optimesh not installed. Falling back to unoptimized grid.")
                    print(
                        "The solution quality can be much worse because of the missing smoothing."
                    )
                    print("==========================================================")

            graph = self.mesh_to_graph(X, cells)
        G = select_largest_component(graph)
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
        return (
            f"GmshGrid(full_coverage={self.full_coverage},"
            f" point_based={self.point_based}, quad={self.quad}, alg={self.alg},"
            f" opt={self.opt_method}, scale={self.scale}, buffer={self.buffer},"
            f" simplification={self.simplification}, iterations={self.iterations}, "
            f"hard_corners={self.hard_corners}, hole_workaround{self.hole_workaround})"
        )
