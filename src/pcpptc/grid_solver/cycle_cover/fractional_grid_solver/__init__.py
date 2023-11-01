"""

THIS DOCUMENTATION IS PROBABLY OUTDATED!

Computes an optimal fractional solution for cycle_cover cover with turn and distance costs for
embedded graphs, i.target., grids. The vertices of the graph must be waypoints with `.x`,`.y`,
`__hash__`, and `__lt__`. The graph should be a networkx graph.

Create some graph
```
import networkx as nx
G = nx.Graph()
G.add_nodes_from([p0, p1, p2])
G.add_edges_from([(p0, p1), (p1, p2), (p0, p2)])
```

Select an touring_costs
```
from fractional_grid_solver import TouringCosts, PointBasedInstance, FractionalSolution,\
                                    FractionalGridSolver, VertexPassage
obj = TouringCosts(distance_cost=0.0, turn_cost=1.0)
obj.penalties[p0] = 0.0
obj.penalties[p1] = 0.0
```

Solve
```
polygon = PointBasedInstance(G, obj)
sol = FractionalGridSolver()(polygon)
for vp, x in sol:
    print("VertexPassage:", vp, "Value:", x)
```


"""

from ...grid_instance import PointBasedInstance
from .integralizer import IntegralizingFractionalSolver
from .solver import FractionalGridSolver


def solve(instance: PointBasedInstance):
    return FractionalGridSolver()(instance)


__all__ = ["FractionalGridSolver", "IntegralizingFractionalSolver", "solve"]
