import typing

from optimizer.grid_solver.cycle_connecting import connect_cycles_via_pcst
from optimizer.grid_solver.grid_instance import (
    Cycle,
    MultipliedTouringCosts,
    PointBasedInstance,
)
from optimizer.grid_solver.grid_solution.cycle_solution import create_cycle_solution
from optimizer.instance_converter.graph.graphs import create_unit_graph
from optimizer.instance_converter.polygonal_area import PolygonalArea
from optimizer.polygon_instance import PolygonInstance
from optimizer.solver_selection.offset_coverage.offset_cycle_cover import (
    compute_offset_cycle_cover,
)
from shapely.geometry import Point

from ...grid_solver.grid_solution.create_minimal_instance import (
    create_minimal_graph_from_solution,
)
from ...instance_converter.graph import (
    attach_multiplier_to_graph,
    get_coverage_necessities_from_polygon_instance,
)


class OffsetPolygonSolver:
    def remove_repetitions(self, points: typing.Iterable[Point]) -> typing.List[Point]:
        cleaned_points = []
        for p in points:
            if not cleaned_points or cleaned_points[-1] != p:
                cleaned_points.append(p)
            else:
                print("REPETITION", cleaned_points[-1], p)
                print(cleaned_points)
        while cleaned_points[0] == cleaned_points[-1]:
            print("NOT CLOSED")
            cleaned_points.pop()
        return cleaned_points

    def convert_tour_to_list(self, tour: Cycle) -> typing.List[Point]:
        return [Point(p.x, p.y) for p in tour.iterate_vertices()]

    def __call__(self, pi: PolygonInstance) -> typing.List[Point]:
        pa = PolygonalArea(polygon=pi.feasible_area)
        cc = compute_offset_cycle_cover(pi.feasible_area, pi.tool_radius)
        graph = create_minimal_graph_from_solution(cc)
        graph = create_unit_graph(
            [], 3 * pi.tool_radius, extend_graph=graph, polygon=pa, degree_limit=7
        )
        assert len({p.point for p in graph.nodes}) == graph.number_of_nodes()
        attach_multiplier_to_graph(graph, pi, 0.25 * pi.tool_radius)
        obj = MultipliedTouringCosts(
            graph, distance_factor=pi.distance_cost, turn_factor=pi.turn_cost
        )
        coverage_necessities = get_coverage_necessities_from_polygon_instance(pi, graph)
        pbi = PointBasedInstance(graph, obj, coverage_necessities)
        cc = create_cycle_solution(pbi, cc)
        tour = connect_cycles_via_pcst(pbi, cc)
        for i, p in enumerate(tour.iterate_vertices()):
            assert p != tour.passages[(i + 1) % len(tour)].v
        return self.remove_repetitions(self.convert_tour_to_list(tour))
