from dataclasses import dataclass

from .cycle_connecting import connect_cycles_via_pcst
from .cycle_cover.lns import CcLns, TourLns
from .cycle_cover.solver import CycleCoverSolver, CycleCoverSolverCallbacks
from .grid_instance import PointBasedInstance
from .grid_solution import (
    Cycle,
    FractionalSolution,
    create_cycle_solution,
    is_feasible_cycle_cover,
)


class GridSolverCallbacks:
    def __init__(self):
        self.cc_callbacks = CycleCoverSolverCallbacks()

    def on_grid_solution(self, tour, touring_cost, opportunity_loss):
        pass

    def __repr__(self):
        return "DefaultCallbacks"


@dataclass
class GridSolverParameter:
    k: int = 3
    r: int = 2
    adaptive: bool = True
    integralize: int = 50
    cc_opt_steps: int = 25
    cc_opt_size: int = 50
    t_opt_steps: int = 25
    t_opt_size: int = 50
    callbacks: GridSolverCallbacks = GridSolverCallbacks()


class GridSolver:
    """
    Solves the grid instance and returns a tour.
    TODO: What happens if it is better not to cover anything?
    """

    def __init__(self, **kwargs):
        self.params = GridSolverParameter(**kwargs)
        self.cc_solver = CycleCoverSolver(
            k=self.params.k,
            r=self.params.r,
            adaptive_strips=self.params.adaptive,
            integralize=self.params.integralize,
            callbacks=self.params.callbacks.cc_callbacks,
        )
        self.cc_optimizer = CcLns(self.params.cc_opt_size, self.params.cc_opt_steps)
        self.tour_optimizer = TourLns(self.params.t_opt_size, self.params.t_opt_steps)

    def __str__(self):
        return f"GridSolver({self.params})"

    def description(self) -> str:
        descr = "Grid Solver:\n"
        descr += "==============================\n"
        descr += self.cc_solver.description() + "\n"
        descr += "------------------------------\n"
        descr += self.cc_optimizer.description() + "\n"
        descr += "------------------------------\n"
        descr += self.tour_optimizer.description() + "\n"
        descr += "==============================\n"
        return descr

    def __call__(self, instance: PointBasedInstance) -> Cycle:
        print(self.description())
        print("Instance")
        print("---------------------------------")
        print(f"Vertices: {instance.graph.number_of_nodes()}")
        print(f"Edges: {instance.graph.number_of_edges()}")
        print(f"Max Degree: {max(x[1] for x in instance.graph.degree())}")
        print(
            f"Max value: {max(instance.coverage_necessities[n].opportunity_loss(0.0) for n in instance.graph.nodes)}"
        )
        cc = self.cc_solver.optimize(instance)
        cc = self.cc_optimizer.optimize(instance, cc)
        cc = create_cycle_solution(instance.graph, cc)
        assert is_feasible_cycle_cover(
            instance,
            sum((c.to_fractional_solution() for c in cc), FractionalSolution()),
        )
        tour = connect_cycles_via_pcst(instance, cc)
        if not tour:
            print("Result is empty tour.")
            opportunity_loss = sum(
                instance.coverage_necessities[p].opportunity_loss(0.0)
                for p in instance.graph.nodes
            )
            self.params.callbacks.on_grid_solution(None, 0.0, opportunity_loss)
            return Cycle([])
        assert is_feasible_cycle_cover(instance, tour.to_fractional_solution())
        # cc = create_cycle_solution(instance.graph, tour)
        # assert len(cc)==1
        tour_fs = self.tour_optimizer.optimize(instance, tour.to_fractional_solution())
        tour = create_cycle_solution(instance.graph, tour_fs)
        assert len(tour) <= 1
        tour = tour[0] if tour else Cycle([])
        touring_costs = sum(
            instance.touring_costs.vertex_passage_cost(vp, halving=True)
            for vp in tour.passages
        )
        opportunity_loss = sum(
            instance.coverage_necessities[p].opportunity_loss(tour_fs.coverage(p))
            for p in instance.graph.nodes
        )
        self.params.callbacks.on_grid_solution(tour, touring_costs, opportunity_loss)
        print("Touring costs in grid:", touring_costs)
        print("Opportunity loss in grid:", opportunity_loss)
        return tour
