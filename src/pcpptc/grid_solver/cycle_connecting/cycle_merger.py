from ..grid_instance import PointBasedInstance
from ..grid_solution import Cycle, create_cycle_solution
from .shortest_path import CycleCheapestConnection


class CycleMerger:
    """
    Merges a cycle to a tour via a doubled shortest path.
    The cheapest of such shortest paths is used, including the connection costs at the
    ends.
    """

    def __init__(self, instance: PointBasedInstance, cycle: Cycle):
        self.instance = instance
        self._cheapest_connections = CycleCheapestConnection(instance, cycle)
        self.cycle = cycle

    def merge(self, cycle: Cycle) -> Cycle:
        c = self._cheapest_connections.get_connection(cycle)
        fs = cycle.to_fractional_solution() + self.cycle.to_fractional_solution() + c
        cc = create_cycle_solution(self.instance.graph, fs)
        assert len(cc) == 1
        self.cycle = cc[0]
        self._cheapest_connections.update_cycle(self.cycle)
        return self.cycle

    def estimate_cost(self, target: Cycle) -> float:
        return self._cheapest_connections.get_cost(target)
