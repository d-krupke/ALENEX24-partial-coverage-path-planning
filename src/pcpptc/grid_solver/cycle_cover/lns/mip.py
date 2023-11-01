import gurobipy as gp

from ...grid_instance import PointBasedInstance
from .penalty_variables import PenaltyVariables
from .vp_variables import VertexPassageVariablesInGraph


class MixedIntegerProgram:
    """
    Builds a linear program for a min-turn penalty cycle_cover cover on an embedded graph.
    """

    def __init__(self, instance: PointBasedInstance, area, fs):
        self.instance = instance
        self.area = area
        self.model = gp.Model("fractional_grid_covering_lp")
        self.model.setParam("OutputFlag", 0)
        self.vertex_passage_vars = VertexPassageVariablesInGraph(
            instance=instance, area=area, fractional_solution=fs, model=self.model
        )
        assert all(vp.v in area for vp in self.vertex_passage_vars)
        self.penalty_vars = PenaltyVariables(
            instance=instance, area=area, fractional_solution=fs, model=self.model
        )
        self.build_objective()
        self._build_coverage_constraints()
        self._build_flow_constraints()

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
        for v in self.area:
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
            if e[0] in self.area and e[1] in self.area:
                def m(vp):
                    return 2 if vp.is_uturn() else 1
                vars = self.vertex_passage_vars
                def elements(v, o):
                    return vars.get_outgoing_variables(v, o).items()
                def out(v, o):
                    return sum(m(vp) * var for vp, var in elements(v, o))
                self.model.addConstr(out(e[0], e[1]) - out(e[1], e[0]) == 0)
