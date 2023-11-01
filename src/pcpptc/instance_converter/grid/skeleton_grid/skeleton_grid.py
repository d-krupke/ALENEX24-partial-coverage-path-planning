import typing

import numpy as np
import scipy.spatial
import skgeom as sg
from optimizer.grid_solver.grid_instance import Point, PointVertex
from optimizer.instance_converter.polygonal_area import PolygonalArea

from .convert_to_skgeom_polygon import convert_to_skgeom_polygon
from .points_on_boundary import place_points_on_polygon_boundary


def select_point_vertices_with_min_distance(
    points: typing.Iterable[Point], min_distance: float
):
    points = list(points)
    point_matrix = np.array([p.to_np() for p in points])
    selected = np.array(len(points) * [False], dtype=bool)
    kdtree = scipy.spatial.KDTree(point_matrix)
    for i, p in enumerate(points):
        in_range = kdtree.query_ball_point(point_matrix[i], min_distance)
        if not any(selected[j] for j in in_range):
            selected[i] = True
            yield PointVertex(p)


def compute_skeleton_grid(
    pe: PolygonalArea,
    inward_step_size: float,
    boundary_step_size: float,
    min_distance: float,
    outer_boundary_offset: float = 0.02,
):
    """
    inward_step_size: The offset/step length of moving the boundary lines inwards.
    boundary_step_size: Place on the offset polygons the waypoints with a maximum distance
                        of this
    min_distance: All waypoints should be at least this far apart.
    out_boundary_offset: Placing waypoints directly on the outer boundary can be problematic.
                         They are not really inside the polygon. Thus, we use
                         outer_boundary_offset*inward_step to move the waypoints inside.
    """
    skgeom_polygon = convert_to_skgeom_polygon(pe)
    skeleton = sg.skeleton.create_interior_straight_skeleton(skgeom_polygon)
    i = 0
    grid_points = []
    while True:
        new_points = []
        offset = (
            i * inward_step_size if i > 0 else outer_boundary_offset * inward_step_size
        )
        for offset_polygon in skeleton.offset_polygons(offset):
            for p in place_points_on_polygon_boundary(
                offset_polygon, boundary_step_size
            ):
                new_points.append(p)
        if not new_points:
            break
        else:
            grid_points += new_points
            i += 1
    for p in select_point_vertices_with_min_distance(grid_points, min_distance):
        yield p
