import random

import networkx as nx

from ...grid_instance import PointBasedInstance
from ...grid_solution.fractional_solution import FractionalSolution


class AreaSelector:
    def __init__(self, n: int, only_covered_roots: bool = False):
        self.n = n
        self.only_covered_roots = only_covered_roots

    def description(self) -> str:
        return f"""AreaSelector with area size {self.n}.
         Selects the vertex that in sum with its direct neighbors has the highest
         coverage costs plus opportunity loss.
         """

    def cost_at_vertex(self, gi, fs, node):
        def vp_cost(vp, value):
            return gi.touring_costs.vertex_passage_cost(vp) * value

        passages = fs.at_vertex(node)
        cov = fs.coverage(node)
        op_loss = gi.coverage_necessities[node].opportunity_loss(cov)
        return sum(vp_cost(vp, value) for vp, value in passages.items()) + op_loss

    def rate_vertex(self, gi: PointBasedInstance, fs: FractionalSolution, node):
        def vc(v):
            return self.cost_at_vertex(gi, fs, v)
        return vc(node) + sum(vc(n) for n in gi.graph.neighbors(node))

    def root_vertex(self, gi, fs: FractionalSolution, exclude):
        if self.only_covered_roots:
            candidates = [vp.v for vp, x in fs if vp.v not in exclude and x >= 1.0]
        else:
            candidates = [n for n in gi.graph.nodes if n not in exclude]
        if not candidates:
            print("No candidate for area selection. Choosing randomly.")
            n = [vp.v for vp, x in fs if x >= 1.0]
            if not n:
                print("No used passages. Choosing random point.")
                n = list(gi.graph.nodes)
            return random.choice(n)
        def c(v):
            return self.rate_vertex(gi, fs, v)
        return max(candidates, key=c)

    def bfs_area(self, gi, root):
        area = [root]
        for _v, nbrs in nx.bfs_successors(gi.graph, root):
            for nbr in nbrs:
                if len(area) > self.n:
                    return area
                else:
                    area.append(nbr)
        return area

    def __call__(self, gi, fs, exclude=None):
        if not exclude:
            exclude = []
        root = self.root_vertex(gi, fs, exclude)
        return root, self.bfs_area(gi, root)
