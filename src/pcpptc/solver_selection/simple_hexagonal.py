"""
Provides a set of basic solvers that use a hexagonal grid.
"""

from ..instance_converter import (
    RandomRegularHexagonal,
    RegularHexagonal,
    RotatingRegularHexagonal,
)
from ..instance_converter.hexagon import RotatingHexagonalWithBoundary
from .abstract_solver import PolygonInstanceSolver


class SimpleHexagonAlgorithm(PolygonInstanceSolver):
    """
    Just places a hexagonal grid onto the area and solves the problem within it.
    """

    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(RegularHexagonal(full_coverage, point_based=point_based))

    def identifier(self) -> str:
        return f"SimpleHexagonalAlgorithm({self.problem_converter})"


class RotatingHexagonAlgorithm(PolygonInstanceSolver):
    """
    Rotates a hexagonal grid such that the sum of minimal turn costs for each point
    are minimal and solves the problem on this grid.
    """

    def __init__(self, full_coverage=False, point_based=False, with_boundary=False):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            RotatingRegularHexagonal(
                full_coverage=full_coverage,
                point_based=point_based,
                with_boundary=with_boundary,
            )
        )

    def identifier(self) -> str:
        return f"RotatingHexagonalAlgorithm({self.problem_converter})"


class RandomHexagonAlgorithm(PolygonInstanceSolver):
    """
    Solves a polygonal instances by placing a random hexagonal grid over the area.
    The grid resolution is determined by the parameter `point_based`.
    """

    def __init__(self, full_coverage=False, point_based=False):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            RandomRegularHexagonal(full_coverage=full_coverage, point_based=point_based)
        )

    def identifier(self) -> str:
        return f"RandomHexagonAlgorithm({self.problem_converter})"


class RotatingHexagonalWithBoundaryAlgorithm(PolygonInstanceSolver):
    def __init__(self, full_coverage=False, point_based=False):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            RotatingHexagonalWithBoundary(
                full_coverage=full_coverage, point_based=point_based
            )
        )

    def identifier(self) -> str:
        return f"RandomHexagonalWithBoundaryAlgorithm({self.problem_converter})"
