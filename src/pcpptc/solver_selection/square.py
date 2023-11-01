from ..instance_converter import (
    RandomRegularSquare,
    RegularSquare,
    RotatingRegularSquare,
)
from ..solver_selection.abstract_solver import (
    PolygonInstanceSolver,
)


class SimpleSquareAlgorithm(PolygonInstanceSolver):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(RegularSquare(full_coverage, point_based=point_based))

    def identifier(self) -> str:
        return f"SimpleSquareAlgorithm(fc={self.problem_converter.full_coverage}, pb={self.problem_converter.point_based})"


class RotatingSquareAlgorithm(PolygonInstanceSolver):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(RotatingRegularSquare(full_coverage, point_based=point_based))

    def identifier(self) -> str:
        return f"RotatingSquareAlgorithm(fc={self.problem_converter.full_coverage}, pb={self.problem_converter.point_based})"


class RandomSquareAlgorithm(PolygonInstanceSolver):
    def __init__(self, full_coverage=False, point_based=False):
        super().__init__(RandomRegularSquare(full_coverage, point_based=point_based))

    def identifier(self) -> str:
        return f"RandomSquareAlgorithm(fc={self.problem_converter.full_coverage}, pb={self.problem_converter.point_based})"
