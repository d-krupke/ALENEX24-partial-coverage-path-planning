import abc
import math
import typing

import gurobipy as gp

from ...grid_instance import PointBasedInstance, PointVertex, VertexPassage
from ...grid_solution import FractionalSolution
from .linear_program import LinearProgram
from .solver import get_fractional_solution


class Node:
    def __init__(
        self,
        fractional_solution: FractionalSolution,
        objective_value: float,
        lb: typing.Dict[VertexPassage, int] = None,
        ub: typing.Dict[VertexPassage, int] = None,
    ):
        if not lb:
            lb = {}
        self.lb = lb
        if not ub:
            ub = {}
        self.ub = ub
        self.solution = fractional_solution
        self.objective_value = objective_value

    def _check_if_reasonable_selection(self, vp: VertexPassage):
        val = self.solution[vp]
        if abs(round(val) - val) <= 0.01:
            msg = "Selected branching-passage is already integral."
            raise KeyError(msg)
        if vp in self.lb and math.ceil(val) <= self.lb[vp]:
            msg = "Selected branching-passage introduces no new lower bound."
            raise KeyError(msg)
        if vp in self.ub and math.floor(val) >= self.ub[vp]:
            msg = "Selected branching-passage introduces no new upper bound."
            raise KeyError(msg)

    def branch(
        self, vp: VertexPassage, lp: LinearProgram
    ) -> typing.Tuple["Node", "Node"]:
        self._check_if_reasonable_selection(vp)
        val = self.solution[vp]
        new_lb = self.lb.copy()
        new_lb[vp] = math.ceil(val)
        lb_node = self._create_node(lp, new_lb, self.ub)
        new_ub = self.ub.copy()
        new_ub[vp] = math.floor(val)
        ub_node = self._create_node(lp, self.lb, new_ub)
        return lb_node, ub_node

    def _create_node(self, lp, lb, ub):
        lp.manual_bounds.set_lb(lb)
        lp.manual_bounds.set_ub(ub)
        lp.optimize()
        if lp.model.Status == gp.GRB.OPTIMAL:
            obj = lp.objective_value()
            solution = get_fractional_solution(lp)
            node = Node(solution, obj, lb, ub)
        else:
            node = None
        return node


class BranchingStrategy(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, instance: PointBasedInstance, node: Node, lp: LinearProgram
    ) -> VertexPassage:
        raise NotImplementedError()


class IntGapCostStrategy(BranchingStrategy):
    def __call__(
        self, instance: PointBasedInstance, node: Node, lp: LinearProgram
    ) -> VertexPassage:
        def vp_cost(vp):
            return instance.touring_costs.vertex_passage_cost(vp, halving=True)
        def rel_cost(vpx):
            return self._fractionality(vpx[1]) * vp_cost(vpx[0]) * self._vertex_fractionality(vpx[0].v, node.solution)
        vp, val = max(node.solution, key=rel_cost)
        assert rel_cost((vp, val)) > 0.01, "Should be a higher value"
        return vp

    def _fractionality(self, x):
        return min(x - math.floor(x), math.ceil(x) - x)

    def _vertex_fractionality(self, v: PointVertex, solution: FractionalSolution):
        return sum(
            self._fractionality(val) for vp, val in solution.at_vertex(v).items()
        )


class ReducedCostBranchingStrategy:
    """
    Does not seem to work as the reduced costs always seem to be zero.
    """

    def __call__(
        self, instance: PointBasedInstance, node: Node, lp: LinearProgram
    ) -> VertexPassage:
        def vp_cost(vp):
            return abs(lp.vertex_passage_vars[vp].RC)
        def rel_cost(vpx):
            return self._fractionality(vpx[1]) * vp_cost(vpx[0])
        vp, val = max(node.solution, key=rel_cost)
        assert rel_cost((vp, val)) > 0.01, "Should be a higher value"
        return vp

    def _fractionality(self, x):
        return min(x - math.floor(x), math.ceil(x) - x)


class IntegralizingBnBTree:
    def __init__(
        self, instance: PointBasedInstance, bs: BranchingStrategy = IntGapCostStrategy()
    ):
        self.instance = instance
        self.lp = LinearProgram(instance)
        self.lp.optimize()
        node = Node(get_fractional_solution(self.lp), self.lp.objective_value())
        self.nodes = [node]
        self.branching_strategy = bs
        self.steps = 0

    def _sort_nodes(self):
        self.nodes = sorted(self.nodes, key=lambda n: n.objective_value)

    def branch(self):
        if self.is_integral():
            msg = "Tries to branch but solution already integral."
            raise RuntimeError(msg)
        node = self._pop_best_node()
        vp = self.branching_strategy(self.instance, node, self.lp)
        children = node.branch(vp, self.lp)
        self.steps += 1
        for child in children:
            if child:
                self.nodes.append(child)
        self._sort_nodes()
        return node, vp

    def is_integral(self):
        return self.nodes[0].solution.is_integral()

    def _best_node(self):
        return self.nodes[0]

    def _pop_best_node(self):
        node = self.nodes[0]
        self.nodes = self.nodes[1:]
        return node

    def get_solution(self):
        return self.nodes[0].solution

    def get_objective(self):
        return self.nodes[0].objective_value


class IntegralizingFractionalSolver:
    def __init__(self, depth: int = 10):
        self.depth = depth

    def description(self) -> str:
        descr = "IntegralizingFractionalSolver"
        descr += "Computing a fractional solution with some BnB steps to improve integrality."
        descr += f"Up to {self.depth} BnB steps are performed."
        return descr

    def __call__(
        self, instance: PointBasedInstance, depth=None
    ) -> typing.Tuple[FractionalSolution, float]:
        if depth is None:
            depth = self.depth
        bnb = IntegralizingBnBTree(instance)
        print("Initial fractional solution:", bnb.get_objective())
        for _i in range(depth):
            if bnb.is_integral():
                print("Integral fractional solution:", bnb.get_objective())
                return bnb.get_solution(), bnb.get_objective()
            bnb.branch()
        print("Optimized fractional solution:", bnb.get_objective())
        return bnb.get_solution(), bnb.get_objective()
