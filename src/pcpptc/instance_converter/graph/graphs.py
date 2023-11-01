"""
Contains functions to create graphs for `PointBasedInstance`.
"""

import typing

import networkx as nx
import numpy as np
import scipy.spatial
from shapely.geometry import MultiPoint
from shapely.geometry import Point as sgPoint
from shapely.ops import triangulate

from pcpptc.grid_solver.grid_instance import PointVertex
from pcpptc.utils import Point, distance

from ..polygonal_area import PolygonalArea


def create_delaunay_graph(
    points: typing.List[PointVertex],
    length_limit=None,
    extend_graph: typing.Optional[nx.Graph] = None,
    polygon: typing.Optional[PolygonalArea] = None,
):
    """
    Creates a delaunay graph for a set of waypoints, specified by `waypoints`.
    Additionally, a start graph can be given via `extend_graph` whose nodes have to be
    disjunct to `waypoints`. The delaunay triangulation is computed on the vertices and the
    waypoints. The `length_limit` allows to limit the maximum length of edges and if
    `polygon` is specified, only edges with line of sight are added.
    """
    graph = extend_graph if extend_graph else nx.Graph()
    points += list(graph.nodes)
    if not points:
        msg = "No points given."
        raise ValueError(msg)
    graph.add_nodes_from(points)
    points_to_vertices = {p.point: p for p in points}
    point_set = MultiPoint([sgPoint(p.point.x, p.point.y) for p in points])
    edges = triangulate(point_set, edges=True)
    for e in edges:
        p0 = Point(e.coords[0][0], e.coords[0][1])
        p1 = Point(e.coords[1][0], e.coords[1][1])
        if length_limit and e.length > length_limit:
            continue
        if polygon and not polygon.has_line_of_sight(p0, p1):
            continue
        graph.add_edge(points_to_vertices[p0], points_to_vertices[p1])
    return graph


def create_unit_graph(
    points: typing.List[PointVertex],
    length_limit,
    extend_graph: typing.Optional[nx.Graph] = None,
    degree_limit: typing.Optional[int] = None,
    polygon: typing.Optional[PolygonalArea] = None,
) -> nx.Graph:
    """
        Create a graph with all edges (LoS) within a specific range, specified by
        lenght_limit. As base it can use a point set given by `waypoints` and a graph to be
        extended via `extend_graph` (both possible but need to be disjunctive). Additionally,
        a degree_limit can be specified as sometimes, the graph can become too dense.
    `   If the polygon is not specified, no line of sight check will be performed.

        Thanks to a KDTree, it should be reasonably efficient.
    """
    graph = extend_graph if extend_graph else nx.Graph()
    points += list(graph.nodes)
    point_matrix = np.array([p.point.to_np() for p in points])
    kdtree = scipy.spatial.KDTree(point_matrix)

    def is_edge_allowed(p0, p1):
        if p0 == p1:
            return False
        if distance(p0, p1) > length_limit:
            return False
        if degree_limit and max(graph.degree[p0], graph.degree[p1]) > degree_limit:
            return False
        if polygon and not polygon.has_line_of_sight(p0, p1):
            return False
        return True

    for i, p in enumerate(points):
        in_range = kdtree.query_ball_point(point_matrix[i], length_limit)
        neighbors = [points[j] for j in in_range]
        for n in neighbors:
            if is_edge_allowed(p, n):
                graph.add_edge(p, n)
    return graph


def select_largest_component(graph: nx.Graph) -> nx.Graph:
    return graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
