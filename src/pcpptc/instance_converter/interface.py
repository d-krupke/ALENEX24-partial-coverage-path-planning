import abc

import networkx as nx

from ..grid_solver.grid_instance import (
    CoverageNecessities,
    PointBasedInstance,
    SimpleCoverage,
)
from ..polygon_instance import PolygonInstance
from .graph import get_coverage_necessities_from_polygon_instance
from .graph.graph_attributes import get_coverage_necessities_based_on_voronoi


class PolygonToGridGraphCoveringConverter(abc.ABC):
    def __init__(self, full_coverage=False, voronoi=True):
        self.voronoi = voronoi
        self.full_coverage = full_coverage

    def _get_coverage_necessities(self, graph: nx.Graph, pi: PolygonInstance):
        if self.full_coverage:
            pass
            return CoverageNecessities(SimpleCoverage())
        else:
            if self.voronoi:
                return get_coverage_necessities_based_on_voronoi(pi, graph)
            else:
                return get_coverage_necessities_from_polygon_instance(pi, graph)

    @abc.abstractmethod
    def __call__(self, pi: PolygonInstance) -> PointBasedInstance:
        pass

    @abc.abstractmethod
    def get_recommended_orientation_number(self) -> int:
        pass

    @abc.abstractmethod
    def get_recommended_repetition_number(self) -> int:
        pass

    @abc.abstractmethod
    def identifier(self) -> str:
        pass

    def __repr__(self):
        return self.identifier()

    def __str__(self):
        return self.identifier()
