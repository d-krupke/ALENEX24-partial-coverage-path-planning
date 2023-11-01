import typing

import numpy as np
import scipy.spatial

from pcpptc.grid_solver.grid_instance import PointVertex
from pcpptc.utils import distance


class DensityFilter:
    def __init__(
        self,
        min_distance: float,
        max_neighbors: typing.Optional[int] = None,
        radius: typing.Optional[float] = None,
    ):
        self.min_distance = min_distance
        self.max_neighbors = max_neighbors
        self.radius = radius if radius else self.min_distance

    def __call__(
        self, grid_points: typing.Iterable[PointVertex]
    ) -> typing.Iterable[PointVertex]:
        points = list(grid_points)
        point_matrix = np.array([p.point.to_np() for p in points])
        selected = np.array(len(points) * [False], dtype=bool)
        kdtree = scipy.spatial.KDTree(point_matrix)
        for i, p in enumerate(points):
            in_range = kdtree.query_ball_point(point_matrix[i], self.radius)
            if any(
                (selected[j] and (distance(p, points[j]) < self.min_distance))
                for j in in_range
            ):
                continue
            elif self.max_neighbors is not None:
                if sum(1 if selected[j] else 0 for j in in_range) > self.max_neighbors:
                    continue
            selected[i] = True
            yield p
        print(f"Kept {sum(selected)} of {len(selected)} points.")
