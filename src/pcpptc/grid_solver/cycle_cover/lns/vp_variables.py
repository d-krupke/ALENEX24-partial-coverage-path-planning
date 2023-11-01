import itertools

import gurobipy as gp

from ...grid_instance import PointBasedInstance, VertexPassage
from ...grid_solution import FractionalSolution
from .fixed_edges import FixedEdges


class VertexPassageVariablesInGraph(dict):
    """
    A dict with all the vertex passage variables of a graph.
    It automatically creates the variables during init.
    Additionally it provides some functions to obtain specific subsets of these variables.
    """

    def __init__(
        self,
        instance: PointBasedInstance,
        area,
        fractional_solution: FractionalSolution,
        model: gp.Model,
    ):
        super().__init__()
        self.instance = instance
        self.graph = instance.graph
        self.model = model
        self.area = area
        self.fixed_edges = FixedEdges(area, fractional_solution)
        self.fractional_solution = fractional_solution
        self._add_variables()
        self._add_fixed_constraints()

    def _add_variables(self):
        for v in self.area:
            for u, w in itertools.combinations_with_replacement(
                self.graph.neighbors(v), r=2
            ):
                u_included = u in self.area or self.fixed_edges[(v, u)] > 0
                w_included = w in self.area or self.fixed_edges[(v, w)] > 0
                if u_included and w_included:
                    vp = VertexPassage(v, end_a=u, end_b=w)
                    var = self.model.addVar(vtype=gp.GRB.INTEGER, lb=0.0)
                    var.Start = self.fractional_solution[vp]
                    self[vp] = var

    def _add_fixed_constraints(self):
        for v in self.area:
            for w, n in self.fixed_edges.at_vertex(v):
                def mult(vp):
                    return 2 if vp.is_uturn() else 1
                out_vars = self.get_outgoing_variables(v, out=w).items()
                passage = sum(mult(vp) * x for vp, x in out_vars)
                self.model.addConstr(passage == n)

    def get_variables_of_vertex(self, v) -> dict:
        """
        Returns all variables that cover/pass v.
        """
        result = {}
        for u, w in itertools.combinations_with_replacement(
            self.graph.neighbors(v), r=2
        ):
            vp = VertexPassage(v, end_a=u, end_b=w)
            if vp in self:
                result[vp] = self[vp]
        return result

    def _cost(self, vp: VertexPassage) -> float:
        return self.instance.touring_costs.vertex_passage_cost(vp, halving=True)

    def obj(self):
        return sum(self._cost(vp) * x for (vp, x) in self.items())

    def get_outgoing_variables(self, v, out) -> dict:
        """
        Get all variables that cover/pass `v` and have an exit to `out`.
        Used target.g. for the constrained that for each edge, there has to be an equal usage
        on both sides.
        """
        result = {}
        for n in self.graph.neighbors(v):
            vp = VertexPassage(v, end_a=out, end_b=n)
            if vp in self:
                result[vp] = self[vp]
        return result
