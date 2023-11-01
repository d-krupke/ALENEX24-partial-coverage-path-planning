from ...grid_instance import PointBasedInstance
from ...grid_solution import (
    FractionalSolution,
    is_feasible_cycle_cover,
)
from .area_selector import AreaSelector
from .cycle_elimination import CycleElimination
from .mip import MixedIntegerProgram


def local_optimize_cc_area(
    instance: PointBasedInstance, fractional_solution: FractionalSolution, area
):
    lp = MixedIntegerProgram(instance, area, fractional_solution)
    lp.optimize()
    result = FractionalSolution()
    result += fractional_solution
    for vp, x in lp.vertex_passage_vars.items():
        result[vp] = round(x.X)
    return result


class CcLns:
    def __init__(self, area_size=50, repetitions: int = 10):
        self.area_selector = AreaSelector(area_size)
        self.repetitions = repetitions

    def _opt_step(self, instance, solution, area) -> FractionalSolution:
        opt_solution = local_optimize_cc_area(instance, solution, area)
        assert is_feasible_cycle_cover(instance, opt_solution)
        return opt_solution

    def description(self) -> str:
        descr = "Local Relaxation CC Optimization:\n"
        descr += " - " + self.area_selector.description() + "\n"
        descr += f"- Repeating {self.repetitions} times."
        return descr

    def optimize(
        self, instance: PointBasedInstance, solution: FractionalSolution
    ) -> FractionalSolution:
        excluded = []
        for _i in range(self.repetitions):
            root, area = self.area_selector(instance, solution, exclude=excluded)
            print(f"Optimize CC around {root}.")
            excluded.append(root)
            for n in instance.graph.neighbors(root):
                excluded.append(n)
            opt_solution = self._opt_step(instance, solution, area)
            solution = opt_solution
        return solution


def local_optimize_tour_area(
    instance: PointBasedInstance,
    fractional_solution: FractionalSolution,
    area,
    max_subtour_eliminations,
):
    lp = MixedIntegerProgram(instance, area, fractional_solution)
    ce = CycleElimination(instance, area, lp.model, lp.vertex_passage_vars, lazy=False)
    result = None
    while result is None or ce.separate(result):
        if max_subtour_eliminations < 0:
            print("Not able to connect tour with given number of eliminations.")
            return fractional_solution
        lp.optimize()
        result = FractionalSolution()
        result += fractional_solution
        for vp, x in lp.vertex_passage_vars.items():
            result[vp] = round(x.X)
        max_subtour_eliminations -= 1
    return result


class TourLns:
    def __init__(
        self, area_size=50, repetitions: int = 10, max_subtour_eliminations: int = 10
    ):
        self.area_selector = AreaSelector(area_size, only_covered_roots=True)
        self.max_subtour_eliminations = max_subtour_eliminations
        self.repetitions = repetitions

    def description(self) -> str:
        descr = "Local Relaxation Tour Optimization:\n"
        descr += (
            f"- Like CC version but trying to reconnect unconnected solutions"
            f" up to {self.max_subtour_eliminations} times.\n"
        )
        descr += " - " + self.area_selector.description() + "\n"
        descr += f"- Repeating {self.repetitions} times."
        return descr

    def _opt_step(self, instance, solution, area) -> FractionalSolution:
        opt_solution = local_optimize_tour_area(
            instance, solution, area, self.max_subtour_eliminations
        )
        assert is_feasible_cycle_cover(instance, opt_solution)
        return opt_solution

    def continous_optimization(
        self, instance: PointBasedInstance, solution: FractionalSolution
    ) -> FractionalSolution:
        excluded = []
        for _i in range(self.repetitions):
            root, area = self.area_selector(instance, solution, exclude=excluded)
            print(f"Optimize tour around {root}.")
            excluded.append(root)
            for n in instance.graph.neighbors(root):
                excluded.append(n)
            opt_solution = self._opt_step(instance, solution, area)
            solution = opt_solution
            yield root, area, solution
        return solution

    def optimize(
        self, instance: PointBasedInstance, solution: FractionalSolution
    ) -> FractionalSolution:
        excluded = []
        for _i in range(self.repetitions):
            root, area = self.area_selector(instance, solution, exclude=excluded)
            print(f"Optimize tour around {root}.")
            excluded.append(root)
            for n in instance.graph.neighbors(root):
                excluded.append(n)
            opt_solution = self._opt_step(instance, solution, area)
            solution = opt_solution
        return solution
