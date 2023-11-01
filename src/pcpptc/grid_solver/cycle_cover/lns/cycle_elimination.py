
import gurobipy as gp

from ...grid_instance import VertexPassage
from ...grid_solution import (
    Cycle,
    FractionalSolution,
    create_cycle_solution,
)
from .vp_variables import (
    VertexPassageVariablesInGraph,
)


class CycleElimination:
    def __init__(
        self,
        instance,
        area,
        model: gp.Model,
        vp_vars: VertexPassageVariablesInGraph,
        lazy: bool,
    ):
        self.model = model
        self.vp_vars = vp_vars
        self.instance = instance
        self.area = area
        self.lazy = lazy

    def separate(self, fractional_solution: FractionalSolution):
        # assert is_feasible_cycle_cover(self.instance, fractional_solution)
        print("Checking for cycles in solution.")
        cc = create_cycle_solution(self.instance.graph, fractional_solution)
        print(f"Found {len(cc)} cycles.")
        if len(cc) > 1:
            for c in cc:
                assert c
                self.eliminate(c)
        return len(cc) - 1

    def eliminate(self, cycle):
        el_vp = self.passages_in_area(cycle)[0]
        constr = (
            sum(self.vp_vars[vp] for vp in self.leaving_passages(cycle))
            >= self.vp_vars[el_vp]
        )
        if self.lazy:
            print("Adding lazy subtour elimination constraint.")
            self.model.cbLazy(constr)
        else:
            print("Adding subtour elimination constraint.")
            self.model.addConstr(constr)

    def passages_in_area(self, cycle: Cycle):
        fs = cycle.to_fractional_solution()
        assert fs
        candidates = [vp for vp, x in fs if vp.v in self.area]
        assert (
            candidates
        ), "Should not be empty. Otherwise, there exists a cycle outside the changed area."
        return candidates

    def leaving_passages(self, cycle: Cycle):
        fs = cycle.to_fractional_solution()
        for vp in self.passages_in_area(cycle):
            for n0 in vp.endpoints():
                for n1 in self.instance.graph.neighbors(vp.v):
                    vp_ = VertexPassage(vp.v, end_a=n0, end_b=n1)
                    if fs[vp_] == 0 and n1 in self.area:
                        yield vp_
