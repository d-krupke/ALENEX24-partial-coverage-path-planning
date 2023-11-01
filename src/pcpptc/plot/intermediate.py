import typing

import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import networkx as nx

from ..grid_solver.grid_instance import VertexPassage
from ..grid_solver.grid_solution import FractionalSolution
from ..instance_converter.polygonal_area import PolygonalArea
from ..utils import Point


def plot_points(
    ax: plt.Axes, points: typing.Iterable[Point], marker="x", color="blue", size=None
):
    if size:
        ax.scatter(
            [p[0] for p in points],
            [p[1] for p in points],
            marker=marker,
            zorder=2,
            color=color,
            s=size,
        )
    else:
        ax.scatter(
            [p[0] for p in points],
            [p[1] for p in points],
            marker=marker,
            zorder=2,
            color=color,
        )


def plot_edges(ax: plt.Axes, edges, color="gray", alpha=0.7, linewidth=1):
    for e in edges:
        p0 = e[0]
        p1 = e[1]
        ax.plot(
            [p0[0], p1[0]],
            [p0[1], p1[1]],
            color=color,
            alpha=alpha,
            linewidth=linewidth,
            solid_capstyle="round",
            zorder=2,
        )


def plot_graph(
    ax: plt.Axes,
    graph: nx.Graph,
    edge_color="gray",
    vertex_color="blue",
    marker="x",
    alpha=1.0,
    linewidth=1,
    size=None,
):
    plot_points(ax, graph.nodes, marker=marker, color=vertex_color, size=size)
    plot_edges(ax, graph.edges, color=edge_color, alpha=alpha, linewidth=linewidth)


def plot_turn(ax, p0, p1, p2, w=1.0, color="black", zorder=2, alpha=1.0):
    start_bc = (0.5 * (p0.x + p1.x), 0.5 * (p0.y + p1.y))
    end_bc = (0.5 * (p2.x + p1.x), 0.5 * (p2.y + p1.y))
    pp1 = mpatches.PathPatch(
        mpath.Path(
            [start_bc, (p1.x, p1.y), end_bc],
            [mpath.Path.MOVETO, mpath.Path.CURVE3, mpath.Path.CURVE3],
        ),
        fc="none",
        transform=ax.transData,
        lw=w,
        color=color,
        zorder=zorder,
        alpha=alpha,
    )
    ax.add_patch(pp1)


def plot_environment(ax: plt.Axes, pe: PolygonalArea):
    ax.plot(
        *pe._shapely_polygon.exterior.xy,
        color="#6699cc",
        alpha=0.7,
        linewidth=3,
        solid_capstyle="round",
        zorder=2,
    )
    for interior in pe._shapely_polygon.interiors:
        ax.plot(
            *interior.xy,
            color="#6699cc",
            alpha=0.7,
            linewidth=3,
            solid_capstyle="round",
            zorder=2,
        )


def plot_fractional_solution(
    ax: plt.Axes,
    sol: FractionalSolution,
    color="black",
    linewidth=1.0,
    zorder=2,
    alpha=1.0,
):
    for vp, x in sol:
        vp: VertexPassage
        x: float
        if x > 0.01:
            lw = x if vp.end_a != vp.end_b else 2 * x
            plot_turn(
                ax,
                vp.end_a,
                vp.v,
                vp.end_b,
                lw * linewidth,
                color=color,
                zorder=zorder,
                alpha=alpha,
            )
