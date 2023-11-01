import networkx as nx

from .fractional_solution import FractionalSolution


def create_minimal_graph_from_solution(solution: FractionalSolution) -> nx.Graph:
    """
    Creates a graph that exactly fits the solution. I.e. it contains exactly the edges
    and vertices used by the vertex passage in the solution.
    """
    graph = nx.Graph()
    graph.add_nodes_from(solution.vertices())
    for vp, _x in solution:
        for n in vp.endpoints():
            graph.add_edge(vp.v, n)
    return graph
