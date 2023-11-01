import itertools

import networkx as nx
import numpy as np

from ..grid_solution import Cycle


def solve_pcst(
    graph: nx.Graph, edge_weight_label: str, vertex_prize_label: str
) -> nx.Graph:
    """
    Solves the PCST on nice networkx graphs.
    """
    mip = PcstMip(graph, edge_weight_label, vertex_prize_label)
    return mip.solve()


def solve_pcst_via_approx(
    graph: nx.Graph, edge_weight_label: str, vertex_prize_label: str
) -> nx.Graph:
    import pcst_fast

    vertices = list(graph.nodes)
    vertex_ids = {v: i for i, v in enumerate(graph.nodes)}
    vertex_prizes = np.array(
        [graph.nodes[v][vertex_prize_label] for v in vertices], dtype=np.float64
    )
    edges = np.array(
        [[vertex_ids[v], vertex_ids[w]] for (v, w) in graph.edges], np.int64
    )
    edge_weights = np.array(
        [data[edge_weight_label] for v, w, data in graph.edges(data=True)],
        dtype=np.float64,
    )
    root = -1
    num_clusters = 1
    pruning = "strong"
    pcst_vertices, pcst_edges = pcst_fast.pcst_fast(
        edges, vertex_prizes, edge_weights, root, num_clusters, pruning, 0
    )
    pcst_graph = nx.Graph()
    for i in pcst_vertices:
        v = vertices[i]
        pcst_graph.add_node(
            v, **{vertex_prize_label: graph.nodes[v][vertex_prize_label]}
        )
    for i in pcst_edges:
        e = edges[i]
        (v, w) = vertices[e[0]], vertices[e[1]]
        weight = graph.edges[v, w][edge_weight_label]
        pcst_graph.add_edge(
            vertices[e[0]], vertices[e[1]], **{edge_weight_label: weight}
        )
    return pcst_graph


import gurobipy as grb


class PcstMip:
    def __init__(
        self, graph: nx.Graph, edge_weight_label: str, vertex_prize_label: str
    ):
        print(f"PCST Mip with {graph.number_of_nodes()} nodes.")
        print("Values:", [graph.nodes[n][vertex_prize_label] for n in graph.nodes])
        self.graph = graph
        self.model = grb.Model()
        self.model.setParam("OutputFlag", 0)

        def is_mandatory(n):
            p = graph.nodes[n][vertex_prize_label]
            return p == float("inf")

        def price(n):
            p = graph.nodes[n][vertex_prize_label]
            if p < float("inf"):
                return -p
            assert is_mandatory(n)
            return 0.0

        self._node_vars = {
            n: self.model.addVar(0, 1.0, obj=price(n), vtype=grb.GRB.BINARY)
            for n in graph.nodes
        }
        self._edge_vars = {
            self._ue(e): self.model.addVar(
                0, 1.0, obj=graph.edges[e][edge_weight_label], vtype=grb.GRB.BINARY
            )
            for e in graph.edges
        }
        for n in graph.nodes:
            if is_mandatory(n):
                self.model.addConstr(self._node_vars[n] == 1)
            constr = (
                sum(self._get_edge_var(e) for e in graph.edges(n))
                <= self._node_vars[n] * graph.number_of_nodes()
            )
            self.model.addConstr(constr)
        constr = sum(self._edge_vars.values()) == sum(self._node_vars.values()) - 1
        self.model.addConstr(constr)

    def _ue(self, e):
        return (min(e, key=hash), max(e, key=hash))

    def solve(self):
        self.model.optimize()
        g = self.extract_pcst()
        cmps = list(nx.connected_components(g))
        if len(cmps) > 1:
            for i, j in itertools.combinations(range(len(cmps)), 2):
                v0 = list(cmps[i])[0]
                v1 = list(cmps[j])[0]
                outgoing = []
                for e in self.graph.edges(cmps[i]):
                    if e[0] not in cmps[i] or e[1] not in cmps[i]:
                        outgoing.append(e)
                constr = (
                    sum(self._get_edge_var(e) for e in outgoing)
                    >= self._node_vars[v0] + self._node_vars[v1] - 1
                )
                self.model.addConstr(constr)
            return self.solve()
        else:
            print(f"Selected {g.number_of_nodes()} cycles.")
            return g

    def extract_pcst(self):
        g = nx.Graph()
        for n, x in self._node_vars.items():
            assert type(n) is Cycle
            if round(x.X) == 1.0:
                g.add_node(n)
        for e, x in self._edge_vars.items():
            if round(x.X) == 1.0:
                assert type(e[0]) is Cycle
                assert type(e[1]) is Cycle
                g.add_edge(e[0], e[1])
        return g

    def _get_edge_var(self, e):
        return self._edge_vars[self._ue(e)]
