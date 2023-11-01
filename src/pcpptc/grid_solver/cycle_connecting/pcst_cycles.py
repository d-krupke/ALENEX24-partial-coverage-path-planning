import typing

import networkx as nx

from ..grid_instance import PointBasedInstance
from ..grid_solution import Cycle, is_feasible_cycle_cover
from .cycle_merger import CycleMerger
from .cycle_penalty_accumulation import calculate_cycle_penalties
from .pcst_solver import solve_pcst


def _cycle_connecting_costs(
    instance: PointBasedInstance, cycle_cover: typing.List[Cycle]
) -> typing.Dict[typing.Tuple[int, int], float]:
    costs = {}
    for i, cycle_a in enumerate(cycle_cover):
        cycle_merge = CycleMerger(instance, cycle_a)
        for j, cycle_b in enumerate(cycle_cover):
            if j <= i:
                continue
            c = cycle_merge.estimate_cost(cycle_b)
            costs[(i, j)] = 2 * c
    return costs


def _compute_connection_graph(
    instance: PointBasedInstance,
    cycle_cover: typing.List[Cycle],
    cycle_merger: typing.Optional[typing.Dict[Cycle, CycleMerger]] = None,
) -> nx.Graph:
    cycle_penalties = calculate_cycle_penalties(
        instance, cycle_cover, substract_touring_costs=True
    )
    graph = nx.Graph()
    for cycle in cycle_cover:
        graph.add_node(cycle, **{"prize": cycle_penalties[cycle]})

    for i, cycle_a in enumerate(cycle_cover):
        if cycle_merger and cycle_a in cycle_merger:
            cycle_merge = cycle_merger[cycle_a]
        else:
            cycle_merge = CycleMerger(instance, cycle_a)
        for j, cycle_b in enumerate(cycle_cover):
            if j <= i:
                continue
            c = cycle_merge.estimate_cost(cycle_b)
            graph.add_edge(cycle_a, cycle_b, weight=c)
    return graph


class CycleMergeGraph:
    def __init__(self, instance: PointBasedInstance, cycle_cover: typing.List[Cycle]):
        self.instance = instance
        self.cycle_cover = list(cycle_cover)
        self._cycle_merger = {
            cycle: CycleMerger(instance, cycle) for cycle in cycle_cover
        }
        self._refer = {}

    def get_cost_graph(self) -> nx.Graph:
        graph = _compute_connection_graph(
            self.instance, self.cycle_cover, self._cycle_merger
        )
        return graph

    def _resolve(self, cycle: Cycle) -> Cycle:
        if cycle not in self._refer:
            return cycle
        return self._resolve(self._refer[cycle])

    def merge(self, cycle_a, cycle_b) -> Cycle:
        cycle_a = self._resolve(cycle_a)
        cycle_b = self._resolve(cycle_b)
        if cycle_a is cycle_b:
            return cycle_a
        cm = self._cycle_merger[cycle_a]
        merged_cycle = cm.merge(cycle_b)
        for c in (cycle_a, cycle_b):
            self.cycle_cover.remove(c)
            self._cycle_merger.pop(c)
            self._refer[c] = merged_cycle
        self.cycle_cover.append(merged_cycle)
        self._cycle_merger[merged_cycle] = cm
        return merged_cycle


def _compute_pcst_on_cycles(cmg: CycleMergeGraph) -> nx.Graph:
    graph = cmg.get_cost_graph()
    bad_cycles = [c for c, prize in graph.nodes(data="prize") if prize < 0]
    for c in bad_cycles:
        graph.remove_node(c)
    if graph.number_of_nodes() > 1:
        assert graph.number_of_edges() >= 1
        pcst = solve_pcst(graph, edge_weight_label="weight", vertex_prize_label="prize")
        return pcst
    else:
        return graph


def _greedy_connect_free(cmg: CycleMergeGraph):
    graph = cmg.get_cost_graph()
    edges = sorted(graph.edges, key=lambda e: graph[e[0]][e[1]]["weight"])
    for e in edges:
        if graph[e[0]][e[1]]["weight"] < 0:
            cmg.merge(e[0], e[1])
    return cmg.cycle_cover


def _merge(pcst: nx.Graph, instance: PointBasedInstance) -> Cycle:
    assert pcst.number_of_nodes() > 0
    cycles = list(pcst.nodes())
    if pcst.number_of_nodes() == 1:
        return cycles[0]
    cycle_merger = CycleMerger(instance, cycles[0])
    for c in nx.dfs_postorder_nodes(pcst, cycles[0]):
        if c != cycles[0]:
            cycle_merger.merge(c)
    return cycle_merger.cycle


def connect_cycles_via_pcst(
    instance: PointBasedInstance, cycle_cover: typing.List[Cycle]
) -> typing.Optional[Cycle]:
    """
    Uses the method from the original approximation algorithm to compute a pcst
    on the cycles (connection costs as edge weights and accumulates penalties as prizes)
    and connect the cycles in the pcst.
    """
    if not cycle_cover:
        return None
    assert len(cycle_cover) >= 1, "There should be cycles to merge"
    if len(cycle_cover) == 1:
        print("Solution is already connected! :)")
        return cycle_cover[0]
    print(f"Connecting {len(cycle_cover)} cycles")
    cmg = CycleMergeGraph(instance, cycle_cover)
    print("Trying to connect greedily")
    _greedy_connect_free(cmg)
    print(f"{len(cmg.cycle_cover)} cycles remaining")
    print("Computing PCST")
    pcst = _compute_pcst_on_cycles(cmg)
    if pcst.number_of_nodes() == 0:
        return None
    assert nx.is_connected(pcst), "PCST should be connected."
    print("Connecting PCST via DFS")
    tour = _merge(pcst, instance)
    assert is_feasible_cycle_cover(
        instance=instance, solution=tour.to_fractional_solution()
    )
    return tour
