import typing

from ..grid_instance import PointBasedInstance
from ..grid_solution import (
    Cycle,
    FractionalSolution,
    create_cycle_solution,
)
from .atomic_strip_matcher import AtomicStripMatching, TransitionCostCalculator
from .atomic_strip_orientation import (
    EquiangularRepetitionAtomicStrips,
    NeighborBasedStripStrategy,
)
from .fractional_grid_solver import FractionalGridSolver, IntegralizingFractionalSolver


class CycleCoverSolverCallbacks:
    def on_fractional_solution(self, fractional_solution, objective):
        pass

    def __repr__(self):
        return "DefaultCallbacks"


class CycleCoverSolver:
    def __init__(
        self,
        k: int = 3,
        r: int = 2,
        adaptive_strips=False,
        integralize: int = 0,
        callbacks=CycleCoverSolverCallbacks(),
    ):
        self.callbacks = callbacks
        if integralize:
            self._lp_solver = IntegralizingFractionalSolver(integralize)
        else:
            self._lp_solver = FractionalGridSolver()

        if adaptive_strips:
            self._atomic_strip_selector = NeighborBasedStripStrategy(k * r)
        else:
            self._atomic_strip_selector = EquiangularRepetitionAtomicStrips(
                number_of_different_orientations=k, reptition_of_each_orientation=r
            )

    def description(self) -> str:
        descr = "Cycle Cover Solver:\n"
        descr += (
            "Using linear programming and blossom matching to compute a cycle"
            " cover with turn-aware, heterogeneous touring costs.\n"
        )
        descr += self._lp_solver.description() + "\n"
        descr += self._atomic_strip_selector.description()
        return descr

    def _create_atomic_strips(self, pbi: PointBasedInstance, frac: FractionalSolution):
        atomic_strips = self._atomic_strip_selector(pbi, frac)
        return atomic_strips

    def _solve_fractionally(self, pbi: PointBasedInstance) -> FractionalSolution:
        fractional_solution, frac_obj = self._lp_solver(pbi)
        self.callbacks.on_fractional_solution(fractional_solution, frac_obj)
        print("Fractional solution:", frac_obj)
        return fractional_solution

    def __call__(self, pbi: PointBasedInstance) -> typing.List[Cycle]:
        solution = self.optimize(pbi)
        cc = create_cycle_solution(pbi.graph, solution)
        return cc

    def optimize(self, pbi: PointBasedInstance) -> FractionalSolution:
        print("Cycle Cover: Computing fractional solution...")
        fractional_solution = self._solve_fractionally(pbi)
        print("Cycle Cover: Creating matching problem...")
        atomic_strips = self._create_atomic_strips(pbi, fractional_solution)
        print("Cycle Cover: Solving matching...")
        solution = self._match_atomic_strips(pbi, atomic_strips)
        return solution

    def _match_atomic_strips(self, pbi, atomic_strips) -> FractionalSolution:
        asm = AtomicStripMatching(
            pbi.graph, TransitionCostCalculator(pbi.touring_costs)
        )
        for p in pbi.graph.nodes:
            for o in atomic_strips[p]:
                s = asm.create_atomic_strip(p, o.orientation)
                if o.is_skippable():
                    asm.add_skip_penalty(s, o.penalty)
        edges = asm.solve()
        solution = asm.to_solution()
        return solution
