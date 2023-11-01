import typing

from ...grid_instance import PointBasedInstance
from ...grid_solution import FractionalSolution
from .linear_program import LinearProgram


def get_fractional_solution(lp: LinearProgram):
    result = FractionalSolution()
    for vp, x in lp.vertex_passage_vars.items():
        if x.x > 0.01:
            result[vp] = x.x
    return result


class FractionalGridSolver:
    """
    Solves the optimal fractional penalty cycle_cover cover with distance and turn costs for
    an embedded graph, target.g., a grid.
    """

    def __init__(self):
        pass

    def description(self) -> str:
        return "FractionalGridSolver based on Gurobi."

    def __call__(
        self, instance: PointBasedInstance
    ) -> typing.Tuple[FractionalSolution, float]:
        lp = LinearProgram(instance)
        lp.optimize()
        return get_fractional_solution(lp), lp.objective_value()
