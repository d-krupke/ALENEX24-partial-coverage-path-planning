import math

import networkx as nx
import numpy as np
import shapely.errors
from shapely.geometry import Point

from pcpptc.grid_solver import PointVertex
from pcpptc.grid_solver.grid_instance.coverage_necessity import (
    CoverageNecessities,
    OptionalCoverage,
    PenaltyCoverage,
)
from pcpptc.polygon_instance import PolygonInstance


def attach_multiplier_to_graph(
    graph: nx.Graph, pi: PolygonInstance, edge_sampling_resolution: float
) -> None:
    node_values = {
        pv: pi.get_multiplier_at(pv.point.to_shapely()) for pv in graph.nodes
    }
    nx.set_node_attributes(graph, values=node_values, name="multiplier")

    def edge_multiplier(e) -> float:
        p0 = e[0].point.to_shapely()
        p1 = e[1].point.to_shapely()
        return pi.get_multiplier_over_segment(p0, p1, edge_sampling_resolution)

    edge_values = {e: edge_multiplier(e) for e in graph.edges}
    nx.set_edge_attributes(graph, values=edge_values, name="multiplier")


def get_coverage_necessities_from_polygon_instance(
    pi: PolygonInstance, graph: nx.Graph
) -> CoverageNecessities:
    print("WARNING: Using naive method to compute coverage necessities.")
    cn = CoverageNecessities(OptionalCoverage())
    for v in graph.nodes:
        p = sum(v for _, v in pi.get_intersected_penalty_polygons(v.point.to_shapely()))
        if p > 0.0:
            p *= math.pi * (pi.tool_radius**2)
            cn[v] = PenaltyCoverage(p)
    return cn


def create_neighbor_based_area(p: PointVertex, graph: nx.Graph, pi: PolygonInstance):
    pos = np.array([p.x, p.y])
    nbrs = np.array([[n.x, n.y] for n in graph.neighbors(p)])
    nbr_dists = np.array([np.linalg.norm(n - pos) for n in nbrs])
    d = min(pi.tool_radius * 4, float(np.mean(nbr_dists)))
    voronoi_cell = Point(p.x, p.y).buffer(d, resolution=4)
    return voronoi_cell


def get_voronoi_cells(pi: PolygonInstance, graph: nx.Graph):
    points = list(graph.nodes)
    array = np.array([[p.x, p.y] for p in points])
    from geovoronoi import voronoi_regions_from_coords

    try:
        region_polys, region_pts = voronoi_regions_from_coords(array, pi.original_area)
    except shapely.errors.TopologicalError as te:
        print(
            "Topological problems with voronoi value estimation. Trying perturbation."
        )
        array += np.random.normal(0, 0.01 * pi.tool_radius, array.shape)
        region_polys, region_pts = voronoi_regions_from_coords(array, pi.original_area)
    voronoi_cells = {points[region_pts[i][0]]: p for i, p in region_polys.items()}
    repair_voronoi_cells(voronoi_cells, graph, pi)
    return voronoi_cells


def repair_voronoi_cells(voronoi_cells: dict, graph, pi):
    for p in voronoi_cells:
        voronoi_cell = voronoi_cells[p]
        if not voronoi_cell.contains(Point(p.x, p.y)):
            print(f"Numerical problems for Voronoi-cell of {p}. Using workaround.")
            voronoi_cell = create_neighbor_based_area(p, graph, pi)
        if voronoi_cell.area > (pi.tool_radius * 4) ** 2:
            print(
                f"Warning: Voronoi cell at {p} unexpected large ({voronoi_cell.area}."
                f" Replacing with workaround"
            )
            voronoi_cell = create_neighbor_based_area(p, graph, pi)
        voronoi_cells[p] = voronoi_cell
        assert voronoi_cell.area < float("inf")


def get_coverage_necessities_based_on_voronoi(
    pi: PolygonInstance, graph: nx.Graph
) -> CoverageNecessities:
    cn = CoverageNecessities(OptionalCoverage())
    voronoi_cells = get_voronoi_cells(pi, graph)
    for p, voronoi_cell in voronoi_cells.items():
        cn[p] = PenaltyCoverage(pi.compute_value_of_area(voronoi_cell))
    return cn
