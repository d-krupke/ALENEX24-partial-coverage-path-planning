import abc
import typing

import networkx as nx

from pcpptc.utils import Point, distance, turn_angle

from .point import PointVertex
from .vertex_passage import VertexPassage


class TouringCosts(abc.ABC):
    @abc.abstractmethod
    def vertex_passage_cost(
        self,
        vp: VertexPassage,
        halving: bool = True,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        pass

    @abc.abstractmethod
    def turn_cost_at_vertex(
        self,
        at: PointVertex,
        ends: typing.Optional[
            typing.Tuple[
                typing.Union[PointVertex, Point], typing.Union[PointVertex, Point]
            ]
        ] = None,
        angle: typing.Optional[float] = None,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        pass

    @abc.abstractmethod
    def distance_cost_of_edge(self, p0: PointVertex, p1: PointVertex) -> float:
        pass


class SimpleTouringCosts(TouringCosts):
    def __init__(self, turn_factor: float, distance_factor: float):
        self.turn_factor = turn_factor
        self.distance_factor = distance_factor

    def vertex_passage_cost(
        self,
        vp: VertexPassage,
        halving: bool = True,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        turn_costs = self.turn_cost_at_vertex(
            vp.v, ends=vp.endpoints(), forced_orientation=forced_orientation
        )

        distance_costs = sum(
            self.distance_cost_of_edge(vp.v, n) for n in vp.endpoints()
        )
        if halving:
            distance_costs *= 0.5
        return distance_costs + turn_costs

    def turn_cost_at_vertex(
        self,
        at: PointVertex,
        ends: typing.Optional[
            typing.Tuple[
                typing.Union[PointVertex, Point], typing.Union[PointVertex, Point]
            ]
        ] = None,
        angle: typing.Optional[float] = None,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        if angle is None:
            if ends is None:
                msg = "Either angle or ends must be provided."
                raise ValueError(msg)
            turn = turn_angle(
                v0=ends[0],
                v1=at,
                v2=ends[1],
                forced_orientation_at_v1=forced_orientation,
            )
        else:
            if forced_orientation:
                msg = "Cannot used forced orientation with angle."
                raise ValueError(msg)
            turn = angle
        return self.turn_factor * turn

    def distance_cost_of_edge(self, p0: PointVertex, p1: PointVertex) -> float:
        dist = distance(p0, p1)
        return self.distance_factor * dist


class MultipliedTouringCosts(TouringCosts):
    def __init__(self, graph: nx.Graph, turn_factor: float, distance_factor: float):
        self.graph = graph
        self._turn_factor = turn_factor
        self._distance_factor = distance_factor

    def vertex_passage_cost(
        self,
        vp: VertexPassage,
        halving: bool = True,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        turn_costs = self.turn_cost_at_vertex(
            vp.v, ends=vp.endpoints(), forced_orientation=forced_orientation
        )

        distance_costs = sum(
            self.distance_cost_of_edge(vp.v, n) for n in vp.endpoints()
        )
        if halving:
            distance_costs *= 0.5
        return distance_costs + turn_costs

    def turn_cost_at_vertex(
        self,
        at: PointVertex,
        ends: typing.Optional[
            typing.Tuple[
                typing.Union[PointVertex, Point], typing.Union[PointVertex, Point]
            ]
        ] = None,
        angle: typing.Optional[float] = None,
        forced_orientation: typing.Optional[float] = None,
    ) -> float:
        if angle is None:
            if ends is None:
                msg = "Either angle or ends must be provided."
                raise ValueError(msg)
            turn = turn_angle(
                v0=ends[0],
                v1=at,
                v2=ends[1],
                forced_orientation_at_v1=forced_orientation,
            )
        else:
            if forced_orientation:
                msg = "Cannot used forced orientation with angle."
                raise ValueError(msg)
            turn = angle
        turn_multiplier = self.graph.nodes[at]["multiplier"]
        return turn_multiplier * self._turn_factor * turn

    def distance_cost_of_edge(self, p0: PointVertex, p1: PointVertex) -> float:
        multiplier = self.graph[p0][p1]["multiplier"]
        dist = distance(p0, p1)
        return self._distance_factor * multiplier * dist
