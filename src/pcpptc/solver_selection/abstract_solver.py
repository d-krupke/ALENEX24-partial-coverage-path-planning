import abc
import typing

import shapely.geometry as slyg

from ..grid_solver.grid_solution import Cycle
from ..grid_solver.grid_solver import GridSolver, GridSolverCallbacks
from ..instance_converter.interface import PolygonToGridGraphCoveringConverter
from ..polygon_instance import PolygonInstance, Solution


def convert_tour_to_list(tour: Cycle) -> typing.List[slyg.Point]:
    return [slyg.Point(p.x, p.y) for p in tour.iterate_vertices(closed=False)]


class PolygonInstanceSolverCallbacks:
    def __init__(self):
        self.grid_callbacks = GridSolverCallbacks()


class PolygonInstanceSolver(abc.ABC):
    """
    Interface for a polygon polygon solver.
    """

    def __init__(
        self,
        problem_converter: PolygonToGridGraphCoveringConverter,
        integralization: int = 50,
        cc_opt_steps: int = 25,
        t_opt_steps: int = 25,
        opt_size: int = 50,
        callbacks=PolygonInstanceSolverCallbacks(),
    ):
        self.problem_converter = problem_converter
        self.grid_solver = GridSolver(
            k=self.problem_converter.get_recommended_orientation_number(),
            r=self.problem_converter.get_recommended_repetition_number(),
            integralize=integralization,
            cc_opt_steps=cc_opt_steps,
            t_opt_steps=t_opt_steps,
            t_opt_size=opt_size,
            cc_opt_size=opt_size,
            callbacks=callbacks.grid_callbacks,
        )

    def __call__(self, pi: PolygonInstance) -> Solution:
        print("Converting polygon instance to grid instance...")
        grid_instance = self.problem_converter(pi)
        grid_tour = self.grid_solver(grid_instance)
        print("Done. Converting to tour.")
        solution = Solution(convert_tour_to_list(grid_tour))
        solution.meta["solver"] = self.identifier()
        return solution

    def __str__(self):
        return self.identifier()

    def __repr__(self):
        return self.identifier()

    @abc.abstractmethod
    def identifier(self) -> str:
        pass
