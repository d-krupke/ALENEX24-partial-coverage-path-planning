import typing

import skgeom as sg

from .convert_skgeom_point import convert_skgeom_point
from .place_points_on_segment import place_points_on_segment


def place_points_on_polygon_with_holes_boundary(
    polygon_with_holes: sg.PolygonWithHoles, max_d: float
):
    boundary_polygon = polygon_with_holes.outer_boundary()
    for p in place_points_on_simple_polygon_boundary(boundary_polygon, max_d):
        yield p
    for hole in polygon_with_holes.holes:
        for p in place_points_on_simple_polygon_boundary(hole, max_d):
            yield p


def place_points_on_simple_polygon_boundary(polygon: sg.Polygon, max_d: float):
    for v in polygon.vertices:
        yield convert_skgeom_point(v)
    for seg in polygon.edges:
        for p in place_points_on_segment(seg, max_d):
            yield p


def place_points_on_polygon_boundary(
    polygon: typing.Union[sg.Polygon, sg.PolygonWithHoles], max_d: float
):
    """
    max_d: Maximal distance between two waypoints. You cannot specify the minimum distance
            because there will be a point on every corner and this depends on the polygon.
    """
    # print("boundary", poly.outer_boundary())
    # print("boundary vertices", list(poly.outer_boundary().vertices))
    # for v in poly.outer_boundary().vertices:
    #    print(v)
    #    yield utils.PointVertex(v.x, v.y)
    if isinstance(polygon, sg.Polygon):
        for p in place_points_on_simple_polygon_boundary(polygon, max_d):
            yield p
    elif isinstance(polygon, sg.PolygonWithHoles):
        for p in place_points_on_polygon_with_holes_boundary(polygon, max_d):
            yield p
    else:
        msg = "Polygon has to be of type skgeom.Polygon or skgeom.PolygonWithHoles."
        raise ValueError(
            msg
        )
