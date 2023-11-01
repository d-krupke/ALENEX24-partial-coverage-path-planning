import skgeom as sg
from optimizer.instance_converter.polygonal_area import PolygonalArea


def convert_to_skgeom_polygon(pe: PolygonalArea) -> sg.PolygonWithHoles:
    """
    Converts a polygonal environment to a PolygonWithHoles of scikit-geometry.
    I am not 100% sure about the orientations. For skgeom the orientation of the waypoints
    seems to be important. I don't know, if they are correct for all polygonal
    environments. If you get problems, maybe that is the reason.
    """
    outer_boundary = [
        sg.Point2(p[0], p[1]) for p in pe._shapely_polygon.exterior.coords
    ]
    holes = []
    for hole in pe._shapely_polygon.interiors:
        hole_boundary = [sg.Point2(p[0], p[1]) for p in hole.coords]
        holes.append(hole_boundary)
    return sg.PolygonWithHoles(
        sg.Polygon(outer_boundary[::-1]), [sg.Polygon(hole[::-1]) for hole in holes]
    )
