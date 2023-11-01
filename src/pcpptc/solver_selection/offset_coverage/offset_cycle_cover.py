# %%
import typing

import shapely
from optimizer.grid_solver import PointVertex
from optimizer.grid_solver.grid_instance import VertexPassage
from optimizer.grid_solver.grid_solution import FractionalSolution
from optimizer.grid_solver.grid_solution.feasibility import is_flow_feasible
from optimizer.utils import distance
from shapely.geometry import Polygon


def _get_polygon_cycles(
    p: Polygon, tool_radius: float
) -> typing.Iterable[shapely.geometry.polygon.Polygon]:
    boundary = p.buffer(-0.05, join_style=2, cap_style=2)
    while boundary:
        if type(boundary) is Polygon:
            yield boundary
        else:
            for p in boundary:
                yield p
        offset_boundary = boundary.buffer(-2 * tool_radius, resolution=4)
        if not offset_boundary:  # not sufficient but will cover more
            offset_boundary = boundary.buffer(-tool_radius, resolution=4)
        boundary = offset_boundary


def _split_boundaries(p: Polygon) -> typing.Iterable[Polygon]:
    yield Polygon(p.exterior.coords)
    for hole in p.interiors:
        yield Polygon(hole.coords)


def _move_to_target(p: PointVertex, target: PointVertex, step_size: float):
    dist = distance(p, target)
    if dist < 2 * step_size:
        step_size = 0.5 * dist
    step = (target.point.to_np() - p.point.to_np()) / dist
    coord = p.point.to_np() + step_size * step
    return PointVertex(coord[0], coord[1])


def _points_on_segment(
    begin: PointVertex, end: PointVertex, max_dist: float
) -> typing.Iterable[PointVertex]:
    assert begin != end
    p = begin
    yield p
    while distance(p, end) > max_dist:
        p = _move_to_target(p, end, max_dist)
        yield p


def _extend_points(
    points: typing.List[PointVertex], max_dist: float
) -> typing.Iterable[PointVertex]:
    for i, p in enumerate(points):
        end = points[(i + 1) % len(points)]
        for pp in _points_on_segment(p, end, max_dist):
            yield pp


def _create_cycle_on_polygon_exterior(
    p: Polygon, max_dist: float
) -> FractionalSolution:
    fs = FractionalSolution()
    points = [PointVertex(coord[0], coord[1]) for coord in p.exterior.coords[:-1]]
    assert len({p.point for p in points}) == len(points), "No duplicates"
    points = list(_extend_points(points, max_dist))
    assert len({p.point for p in points}) == len(points), "No duplicates"
    for i, p in enumerate(points):
        fs.add(
            VertexPassage(
                p,
                end_a=points[(i - 1) % len(points)],
                end_b=points[(i + 1) % len(points)],
            ),
            1.0,
        )
    assert is_flow_feasible(fs)
    return fs


def compute_offset_cycle_cover(p: Polygon, tool_radius: float) -> FractionalSolution:
    """
    Computes a simple offset cycle cover
    """
    fs = FractionalSolution()
    for p in _get_polygon_cycles(p, tool_radius):
        p = p.simplify(0.1 * tool_radius, preserve_topology=True)
        for pp in _split_boundaries(p):
            fs += _create_cycle_on_polygon_exterior(pp, 2 * tool_radius)
    return fs
