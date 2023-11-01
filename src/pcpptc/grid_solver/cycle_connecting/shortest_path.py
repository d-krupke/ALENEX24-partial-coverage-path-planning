import typing

from ..grid_instance import PointBasedInstance, PointVertex, VertexPassage
from ..grid_solution import Cycle, FractionalSolution
from .dedge_dijkstra import DEdge, DEdgeDijkstraTree, EdgeCostFunction
from .intersecting_cycles import IntersectingVertexPassageConnection


class VertexPassageShortestPath:
    """
    Computes the cheapest connection of a vertex passage to a set of vertex passages.
    E.g. you can merge two cycles by adding every vertex passage of the first as source
    and then use the best passage of the second to connect them.
    """

    def __init__(self, instance: PointBasedInstance):
        self._instance = instance
        ecf = EdgeCostFunction(instance, multiplier=2.0)
        self._sources: typing.Dict[DEdge, VertexPassage] = {}
        self._dijkstra = DEdgeDijkstraTree(instance, cost_function=ecf)
        self._direct_connections = IntersectingVertexPassageConnection(instance)

    def _replacement_passages(
        self, vp: VertexPassage, n: PointVertex
    ) -> typing.Tuple[VertexPassage, VertexPassage]:
        return VertexPassage(vp.v, end_a=n, end_b=vp.end_a), VertexPassage(
            vp.v, end_a=n, end_b=vp.end_b
        )

    def _calculate_start_cost(
        self, source: VertexPassage, path_start: PointVertex
    ) -> float:
        vps = self._replacement_passages(source, path_start)
        assert all(vp_.v == source.v for vp_ in vps)

        def cost(vp):
            return self._instance.touring_costs.vertex_passage_cost(vp, halving=False)

        return sum(cost(vp_) for vp_ in vps) - cost(source)

    def add_source(self, source: VertexPassage, propagate=True):
        """
        Adds the vertex passage as source.
        """
        self._direct_connections.add_source(source)
        for n in self._instance.graph.neighbors(source.v):
            e = (source.v, n)
            c = self._calculate_start_cost(source, n)
            if self._dijkstra.update(e, c):
                self._sources[e] = source
        if propagate:
            self.propagate()

    def propagate(self):
        self._dijkstra.propagate()

    def _get_path_costs(self, target: VertexPassage, path_end: DEdge) -> float:
        assert path_end[1] == target.v
        vps = self._replacement_passages(target, path_end[0])
        path_cost = self._dijkstra.cost(path_end)

        def cost(vp):
            return self._instance.touring_costs.turn_cost_at_vertex(
                at=vp.v, angle=vp.turn_angle()
            )

        final_turn_diff = cost(vps[0]) + cost(vps[1]) - cost(target)
        return path_cost + final_turn_diff

    def _get_best_path_end(self, target: VertexPassage) -> typing.Tuple[DEdge, float]:
        candidates = ((n, target.v) for n in self._instance.graph.neighbors(target.v))
        def obj(x):
            return self._get_path_costs(target, x)
        (e, cost) = min(((c, obj(c)) for c in candidates), key=lambda x: x[1])
        return e, cost

    def get_cost(self, target: VertexPassage) -> float:
        direct_costs = self._direct_connections.get_cost(target)
        indirect_costs = self._get_best_path_end(target)[1]
        return min(direct_costs, indirect_costs)

    def _built_fs(
        self, source: VertexPassage, path: typing.List[DEdge], target: VertexPassage
    ) -> FractionalSolution:
        fs = FractionalSolution()
        # add path
        for e, e_ in zip(path[:-1], path[1:]):
            fs.add(VertexPassage(v=e[1], end_a=e[0], end_b=e_[1]), 2.0)
        # replace start
        fs.add(source, -1.0)
        for vp in self._replacement_passages(source, path[0][1]):
            fs.add(vp, 1.0)
        # replace end
        fs.add(target, -1.0)
        for vp in self._replacement_passages(target, path[-1][0]):
            fs.add(vp, 1.0)
        return fs

    def get_connection(
        self, target: VertexPassage
    ) -> typing.Tuple[FractionalSolution, VertexPassage]:
        e, cost = self._get_best_path_end(target)
        if cost > self._direct_connections.get_cost(target):
            return self._direct_connections.get_connection(target)
        else:
            path = self._dijkstra.get_path(e)
            source = self._sources[path[0]]
            return self._built_fs(source=source, path=path, target=target), source


class CycleCheapestConnection:
    """
    For computing the cheapest connection to a reference cycle. It directly returns
    a fractional solution that could be added to the fractional solution of both cycles.
    """

    def __init__(self, instance: PointBasedInstance, cycle: Cycle):
        self._instance = instance
        self._vp_sp = VertexPassageShortestPath(instance)
        self.cycle = cycle
        self.update_cycle(cycle)

    def update_cycle(self, cycle: Cycle):
        """
        Replaces the cycle used for the computations. Expects it to be include most
        parts of the old cycle.
        """
        self.cycle = cycle
        for passage in cycle.passages:
            self._vp_sp.add_source(passage, propagate=False)
        self._vp_sp.propagate()

    def _get_best_target(self, cycle: Cycle) -> typing.Tuple[VertexPassage, float]:
        return min(
            ((vp, self._vp_sp.get_cost(vp)) for vp in cycle.passages),
            key=lambda x: x[1],
        )

    def get_cost(self, cycle: Cycle, check=True) -> float:
        """
        Calculates the costs of connecting the cycle to the reference cycle.
        If check is set to true, it will verify that the path is actually valid.
        When using update, a few paths could become invalid because on vertex passage
        is replaced on every merge.
        """
        target, cost = self._get_best_target(cycle)
        if check:  # if the source of the shortest path really is in the cycle.
            fs, source = self._vp_sp.get_connection(target)
            if source not in self.cycle.passages:
                # Recompute distances
                print(
                    "Recomputing shortest paths. If this happens often, probably buggy."
                )
                self._vp_sp = VertexPassageShortestPath(self._instance)
                self.update_cycle(self.cycle)
                return self.get_cost(cycle, check=False)
        return cost

    def get_connection(self, cycle: Cycle) -> FractionalSolution:
        """
        Returns the fractional solution that allows to merge the cycle with the
        reference cycle.
        """
        target, cost = self._get_best_target(cycle)
        fs, source = self._vp_sp.get_connection(target)
        if source not in self.cycle.passages:
            # Recompute distances
            self._vp_sp = VertexPassageShortestPath(self._instance)
            self.update_cycle(self.cycle)
            return self.get_connection(cycle)
        return fs
