import math


def get_optimal_grid_edge_length(
    triangular: bool, tool_radius: float, point_based: bool
):
    if triangular:
        if point_based:
            return (3 / math.sqrt(3)) * tool_radius
        else:
            return (4 / math.sqrt(3)) * tool_radius
    else:  # square
        if point_based:
            return math.sqrt(2) * tool_radius
        else:
            return 2 * tool_radius
