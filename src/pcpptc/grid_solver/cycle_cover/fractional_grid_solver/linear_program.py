import typing

import gurobipy as gp

from ...grid_instance import PointBasedInstance, VertexPassage
from .penalty_variables import PenaltyVariables
from .vertex_passage_variables import VertexPassageVariablesInGraph


class ManualBounds:
    """
    For manually setting bounds for building your own bnb.
    """

    def __init__(self, model, vertex_passage_vars):
        self.model = model
        self.vertex_passage_vars = vertex_passage_vars
        self._lower_bounds = {}
        self._upper_bounds = {}

    def set_lb(self, lb: typing.Dict[VertexPassage, int]):
        # clean lower bounds
        for vp, bound in list(self._lower_bounds.keys()):
            if vp not in lb or bound > lb[vp]:
                constr = self._lower_bounds.pop((vp, bound))
                self.model.remove(constr)
        # create new lower bounds
        for vp, bound in lb.items():
            if (vp, bound) not in self._lower_bounds:
                x = self.vertex_passage_vars[vp]
                constr = self.model.addConstr(x >= bound)
                self._lower_bounds[(vp, bound)] = constr

    def set_ub(self, ub: typing.Dict[VertexPassage, int]):
        # clean lower bounds
        for vp, bound in list(self._upper_bounds.keys()):
            if vp not in ub or bound < ub[vp]:
                constr = self._upper_bounds.pop((vp, bound))
                self.model.remove(constr)
        # create new lower bounds
        for vp, bound in ub.items():
            if (vp, bound) not in self._upper_bounds:
                x = self.vertex_passage_vars[vp]
                constr = self.model.addConstr(x <= bound)
                self._upper_bounds[(vp, bound)] = constr

    def reset_bounds(self):
        self.set_lb({})
        self.set_ub({})


class LinearProgram:
    """
    Builds a linear program for a min-turn penalty cycle_cover cover on an embedded graph.
    """

    def __init__(self, instance: PointBasedInstance):
        self.instance = instance
        self.model = gp.Model("fractional_grid_covering_lp")
        self.model.setParam("OutputFlag", 0)
        self.vertex_passage_vars = VertexPassageVariablesInGraph(
            instance=instance, model=self.model
        )
        self.penalty_vars = PenaltyVariables(instance=instance, model=self.model)
        self.build_objective()
        self._build_coverage_constraints()
        self._build_flow_constraints()
        self.manual_bounds = ManualBounds(self.model, self.vertex_passage_vars)

    def optimize(self):
        """
        Optimizes the linear program.
        """
        self.model.optimize()

    def objective_value(self) -> float:
        return self.model.getObjective().getValue()

    def build_objective(self):
        """
        Builds the touring_costs. You can call this after changing the positions of the
        vertices without changing the edges.
        """
        touring_costs = self.vertex_passage_vars.obj()
        penalty_costs = self.penalty_vars.obj()
        self.model.setObjective(touring_costs + penalty_costs, gp.GRB.MINIMIZE)

    def _build_coverage_constraints(self):
        """
        Adds a constraint for every vertex that it needs to be covered according to the
        coverage constraints in the polygon.
        """
        for v in self.instance.graph.nodes:
            coverage_necessity = self.instance.coverage_necessities[v]
            t = len(coverage_necessity)
            if t == 0:
                # Doesn't have to be covered
                continue
            cov_sum = sum(self.vertex_passage_vars.get_variables_of_vertex(v).values())
            penalty_vars_of_v = self.penalty_vars[v]
            if len(penalty_vars_of_v) > 0:
                self.model.addConstr(
                    cov_sum + sum(x[0] for x in penalty_vars_of_v) >= t
                )
            else:
                self.model.addConstr(cov_sum >= t)

    def _build_flow_constraints(self):
        for e in self.instance.graph.edges:
            def m(vp):
                return 2 if vp.is_uturn() else 1
            vars = self.vertex_passage_vars
            def elements(v, o):
                return vars.get_outgoing_variables(v, o).items()
            def out(v, o):
                return sum(m(vp) * var for vp, var in elements(v, o))
            self.model.addConstr(out(e[0], e[1]) - out(e[1], e[0]) == 0)
