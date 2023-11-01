import typing

import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
from shapely.geometry import Point
from shapely.plotting import plot_polygon

from ..polygon_instance import Solution
from ..polygon_instance.instance import PolygonInstance


def plot_polygon_instance(
    ax: plt.Axes,
    pi: PolygonInstance,
    set_limits: bool = True,
    plot_valuable_areas: bool = True,
    relative_value=None,
    plot_expensive_areas: bool = True,
    relative_expense=None,
):
    """
    Plots a polygon polygon including the penalty and multiplier areas.
    """
    if set_limits:
        bounds = pi.feasible_area.bounds
        ax.set_xlim(bounds[0] - 2 * pi.tool_radius, bounds[2] + 2 * pi.tool_radius)
        ax.set_ylim(bounds[1] - 2 * pi.tool_radius, bounds[3] + 2 * pi.tool_radius)
    ax.set_facecolor("lightgrey")
    if pi.original_area:
        plot_polygon(
            pi.original_area,
            ax=ax,
            add_points=False,
            facecolor="white",
            edgecolor="black",
            alpha=1.0,
            zorder=1,
        )
        plot_polygon(
            pi.original_area,
            ax=ax,
            add_points=False,
            facecolor="lightgrey",
            edgecolor="black",
            alpha=0.5,
            zorder=1,
        )
        plot_polygon(
            pi.feasible_area,
            ax=ax,
            add_points=False,
            facecolor="white",
            edgecolor="black",
            alpha=1.0,
            zorder=1,
            ls="--",
        )
    else:
        plot_polygon(
            pi.feasible_area,
            ax=ax,
            add_points=False,
            facecolor="white",
            edgecolor="black",
            alpha=1.0,
            zorder=1,
        )
    if plot_valuable_areas:
        if relative_value:
            max_penalty = relative_value
        else:
            max_penalty = max(value for penalty, value in pi.valuable_areas)
        for penalty, value in pi.valuable_areas:
            plot_polygon(
                penalty,
                add_points=False,
                ax=ax,
                facecolor="green",
                edgecolor="green",
                alpha=value / (2 * max_penalty),
                zorder=1,
            )
    if pi.expensive_areas and plot_expensive_areas:
        if relative_expense:
            max_multiplier = relative_expense
        else:
            max_multiplier = sum(value for _, value in pi.expensive_areas)
        for multiplier, value in pi.expensive_areas:
            plot_polygon(
                multiplier,
                add_points=False,
                ax=ax,
                facecolor="red",
                edgecolor="red",
                alpha=value / (2 * max_multiplier),
                zorder=1,
            )


def plot_turn(ax, p0, p1, p2, w=1.0, color="black"):
    start_bc = (0.5 * (p0.x + p1.x), 0.5 * (p0.y + p1.y))
    end_bc = (0.5 * (p2.x + p1.x), 0.5 * (p2.y + p1.y))
    pp1 = mpatches.PathPatch(
        mpath.Path(
            [start_bc, (p1.x, p1.y), end_bc],
            [mpath.Path.MOVETO, mpath.Path.CURVE3, mpath.Path.CURVE3],
        ),
        facecolor="none",
        transform=ax.transData,
        lw=w,
        edgecolor=color,
        zorder=3,
    )
    ax.add_patch(pp1)


def plot_solution(ax: plt.Axes, solution: typing.List[Point], color="black", w=1.0):
    points = solution + solution[:2]
    for i, p in enumerate(points[:-2]):
        plot_turn(ax, p, points[i + 1], points[i + 2], color=color, w=w)


def plot_coverage(ax: plt.Axes, pi: PolygonInstance, solution: Solution, color="blue"):
    print("Computing coverage polygon")
    coverage_poly = solution.coverage_polygon(
        pi.tool_radius * 1.001
    )  # scaling slightly up to prevent degenerated cases.
    print("Plotting coverage polygon")
    plot_polygon(
        coverage_poly,
        ax=ax,
        add_points=False,
        facecolor=color,
        edgecolor=color,
        alpha=0.5,
        zorder=1,
    )
