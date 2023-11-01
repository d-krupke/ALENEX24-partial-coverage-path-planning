import itertools

import gurobipy as gp

from ...grid_instance import PointBasedInstance, VertexPassage


class VertexPassageVariablesInGraph(dict):
    """
    A dict with all the vertex passage variables of a graph.
    It automatically creates the variables during init.
    Additionally it provides some functions to obtain specific subsets of these variables.
    """

    def __init__(self, instance: PointBasedInstance, model: gp.Model):
        super().__init__()
        self.instance = instance
        self.graph = instance.graph
        self.model = model
        for v in self.graph.nodes:
            for u, w in itertools.combinations_with_replacement(
                self.graph.neighbors(v), r=2
            ):
                vp = VertexPassage(v, end_a=u, end_b=w)
                var = model.addVar(vtype=gp.GRB.CONTINUOUS, lb=0.0)
                self[vp] = var

    def get_variables_of_vertex(self, v) -> dict:
        """
        Returns all variables that cover/pass v.
        """
        result = {}
        for u, w in itertools.combinations_with_replacement(
            self.graph.neighbors(v), r=2
        ):
            vp = VertexPassage(v, end_a=u, end_b=w)
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
            result[vp] = self[vp]
        return result
