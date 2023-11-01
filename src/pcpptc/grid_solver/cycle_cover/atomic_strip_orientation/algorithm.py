import typing
import unittest

import networkx as nx

from ...grid_instance import CoverageNecessities, PointVertex, SimpleTouringCosts
from ...grid_solution import FractionalSolution
from ..fractional_grid_solver import FractionalGridSolver, PointBasedInstance
from .assignment import FixedRepetitionAtomicStripAssignment
from .atomic_strip import AtomicStripBlueprint
from .orientation_list_objective import OrientationListObjective
from .orientations import NeighborOrientations, StepwiseOrientations
from .patterns import EquiangularOrientationList


class EquiangularRepetitionAtomicStrips:
    def __init__(
        self, number_of_different_orientations: int, reptition_of_each_orientation: int
    ):
        """
        number_of_different_orientations: Number of equiangular orientations.
            If number_of_different_orientations=2 there will
             be two different orthogonal orientations.
        reptition_of_each_orientation: The repetition of each orientation.
        """
        self.k = number_of_different_orientations
        self.r = reptition_of_each_orientation

    def _get_sample_orientations(self, instance: PointBasedInstance, v: PointVertex):
        stepwise_orientations = StepwiseOrientations(10)
        neighbor_orientations = NeighborOrientations(instance)
        return list(stepwise_orientations()) + list(neighbor_orientations(v))

    def description(self) -> str:
        return (
            f"EquiangularRepetitionalAtomicStrips putting "
            f"{self.k} equiangular atomic strips with {self.r} repeitions on the"
            f" waypoint minimizing the overhead of fitting the fractional solution."
        )

    def __call__(
        self, instance: PointBasedInstance, fractional_solution: FractionalSolution
    ) -> typing.Dict[PointVertex, typing.List[AtomicStripBlueprint]]:
        print("Using static atomic strip selection strategy.")
        pattern = EquiangularOrientationList(self.k)
        obj = OrientationListObjective(instance, fractional_solution)
        assigner = FixedRepetitionAtomicStripAssignment(
            self.r, instance, fractional_solution
        )
        result = {}
        for v in instance.graph.nodes:
            orientations = self._get_sample_orientations(instance, v)
            best_set = min((pattern(o) for o in orientations), key=lambda x: obj(v, x))
            result[v] = list(assigner(v, best_set))
        return result


class FoobarAlgorithmTest(unittest.TestCase):
    def test1(self):
        G = nx.Graph()
        points = [[PointVertex(x, 0.0), PointVertex(x, 1.0)] for x in [0.0, 1.0, 2.0]]
        G.add_nodes_from(p for pp in points for p in pp)
        for x_i in range(len(points)):
            G.add_edge(points[x_i][0], points[x_i][1])
            if x_i > 0:
                for y_i in range(2):
                    G.add_edge(points[x_i][y_i], points[x_i - 1][y_i])
        instance = PointBasedInstance(
            G, SimpleTouringCosts(1.0, 1.0), CoverageNecessities()
        )
        frac_sol = FractionalGridSolver()(instance)
        fa = EquiangularRepetitionAtomicStrips(2, 2)
        print(fa(instance, frac_sol))
