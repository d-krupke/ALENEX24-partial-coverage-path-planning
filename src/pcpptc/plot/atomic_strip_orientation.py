import math
import typing

import matplotlib.pyplot as plt

from ..grid_solver.cycle_cover.atomic_strip_orientation.atomic_strip import (
    AtomicStripBlueprint,
)
from ..grid_solver.grid_instance import PointVertex
from ..utils import Point


def __get_end_points(point, orientation, l):
    p0 = point + l * Point(math.cos(orientation), math.sin(orientation))
    p1 = point + l * Point(
        math.cos(orientation + math.pi), math.sin(orientation + math.pi)
    )
    return p0, p1


def plot_atomic_strips(
    ax: plt.Axes,
    atomic_strips: typing.Dict[PointVertex, typing.List[AtomicStripBlueprint]],
    tool_radius: float,
):
    for p, atomic_strips in atomic_strips.items():
        for o in atomic_strips:
            if o.is_skippable() and not o.has_penalty():
                p0, p1 = __get_end_points(p.point, o.orientation, 0.7 * tool_radius)
                ax.plot([p0.x, p1.x], [p0.y, p1.y], c="orange", ls=":")
        for o in atomic_strips:
            if o.is_skippable() and o.has_penalty():
                p0, p1 = __get_end_points(p.point, o.orientation, 0.8 * tool_radius)
                ax.plot([p0.x, p1.x], [p0.y, p1.y], c="blue", ls="--")
        for o in atomic_strips:
            if not o.is_skippable():
                p0, p1 = __get_end_points(p.point, o.orientation, 0.9 * tool_radius)
                ax.plot([p0.x, p1.x], [p0.y, p1.y], c="red", ls="-")
