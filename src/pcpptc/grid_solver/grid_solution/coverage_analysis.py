import typing

import matplotlib.pyplot as plt
import shapely
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.plotting import plot_polygon

from pcpptc.utils import Point

from .cycle_solution import Cycle


def compute_coverage_polygon_of_grid(
    grid_points: typing.Iterable[Point], tool_radius: float
) -> shapely.geometry.polygon.Polygon:
    """
    Computes the polygon that is covered by the grid (intersection of circles at the
    grid waypoints).
    WARNING: Not sure what happens if it is not connected. The return type may be different.
    """
    circles = [
        shapely.geometry.Point(v.x, v.y).buffer(tool_radius) for v in grid_points
    ]
    covered_area = unary_union(circles)
    return covered_area


def plot_grid_coverage(
    ax: plt.Axes, grid_points: typing.Iterable[Point], tool_radius: float
) -> None:
    """
    Plots the area that is covered by the grid. Note that the actual tour can cover more
    as it also uses the edges. It can be advantageous not to cover everything with the
    grid.
    """
    covered_area = compute_coverage_polygon_of_grid(grid_points, tool_radius)
    plot_polygon(
        covered_area,
        ax=ax,
        add_points=False,
        facecolor="blue",
        edgecolor="blue",
        alpha=0.3,
        zorder=2,
    )


def compute_grid_coverage_area(
    grid_points: typing.Iterable[Point], tool_radius: float
) -> float:
    """
    Computes the area that is covered by the grid (union of circles at the grid waypoints).
    """
    return compute_coverage_polygon_of_grid(grid_points, tool_radius).area


def compute_coverage_polygon_of_tour(
    tour: Cycle, tool_radius: float
) -> shapely.geometry.polygon.Polygon:
    """
    Computes the polygon that is covered by the circle-tool while moving on the tour.
    """
    line = LineString([(v.x, v.y) for v in tour.iterate_vertices(closed=True)])
    dilated = line.buffer(tool_radius, cap_style=1, join_style=1)
    return dilated


def compute_coverage_area_of_tour(tour: Cycle, tool_radius: float) -> float:
    """
    Computes the area that is covered by the tour. Includes the area outside the
    feasibility polygon in which the grid is placed.
    """
    return compute_coverage_polygon_of_tour(tour, tool_radius).area


def plot_tour_coverage(ax: plt.Axes, tour: Cycle, tool_radius: float) -> None:
    """
    Plots the area that is covered by the tour.
    """
    dilated = compute_coverage_polygon_of_tour(tour, tool_radius)
    plot_polygon(
        dilated,
        ax=ax,
        add_points=False,
        facecolor="blue",
        edgecolor="blue",
        alpha=0.3,
        zorder=2,
    )
