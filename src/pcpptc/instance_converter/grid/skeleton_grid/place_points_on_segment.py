import skgeom as sg
from optimizer.grid_solver.grid_instance.point import distance

from .convert_skgeom_point import convert_skgeom_point


def place_points_on_segment(segment: sg.Segment2, max_d: float):
    """
    Will place waypoints with a maximal distance of max_d on a segment. Will assume that
    there are already waypoints on the endpoints of the segment.
    """
    start = convert_skgeom_point(segment.source())
    end = convert_skgeom_point(segment.target())
    l = distance(start, end)
    n = round(l / max_d) - 1
    if n > 0:
        s = l / (n + 1)
        v = (end - start) * (1 / l)  # normalized direction
        for i in range(1, n + 1):
            yield start + i * s * v
