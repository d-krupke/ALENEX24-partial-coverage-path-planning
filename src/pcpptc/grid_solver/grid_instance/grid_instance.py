import networkx as nx

from .coverage_necessity import CoverageNecessities
from .muliplied_touring_costs import TouringCosts


class PointBasedInstance:
    """
    A point based polygon for covering a polygon.
    The graph should use PointVertex as vertices.
    """

    def __init__(
        self,
        graph: nx.Graph,
        touring_costs: TouringCosts,
        coverage_necessities: CoverageNecessities,
    ):
        self.graph = graph
        if not nx.is_connected(graph):
            msg = "Graph has to be connected!"
            raise ValueError(msg)
        self.touring_costs = touring_costs
        self.coverage_necessities = coverage_necessities
