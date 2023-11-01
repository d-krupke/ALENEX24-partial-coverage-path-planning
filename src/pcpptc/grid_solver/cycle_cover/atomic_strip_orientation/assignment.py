"""
Assigning coverage necessities to atomic strips.
"""
import typing

from pcpptc.utils import turn_angle

from ...grid_instance import PointBasedInstance, PointVertex, VertexPassage
from ...grid_solution import FractionalSolution
from .atomic_strip import AtomicStripBlueprint


class FixedRepetitionAtomicStripAssignment:
    """
    Gets a number of orientations and returns reptition_of_each_orientation*|orientations| AtomicStripSuggestions
    where each orientation appears reptition_of_each_orientation-times.
    """

    def __init__(
        self,
        r: int,
        instance: PointBasedInstance,
        fractional_solution: FractionalSolution,
    ):
        self.r = r  # repetitions of each orientation
        self.instance = instance
        self.fractional_solution = fractional_solution

    def _vp_obj(self, vp: VertexPassage, o: float):
        return abs(
            turn_angle(vp.end_a, vp.v, vp.end_b)
            - turn_angle(vp.end_a, vp.v, vp.end_b, forced_orientation_at_v1=o)
        )

    def _assign_vertex_passage_to_orientation(
        self, vp: VertexPassage, orientations: typing.List[float]
    ):
        return min(
            range(len(orientations)), key=lambda i: self._vp_obj(vp, orientations[i])
        )

    def __call__(self, v: PointVertex, orientations: typing.List[float]):
        orientation_weights = len(orientations) * [0.0]
        number_of_usages = len(orientations) * [0]
        vertex_passages = self.fractional_solution.at_vertex(v)
        for vp, x in vertex_passages.items():
            orientation_weights[
                self._assign_vertex_passage_to_orientation(vp, orientations)
            ] += x
        pen_vec = list(self.instance.coverage_necessities[v].penalty_vector)
        pen_vec += (len(orientations) * self.r - len(pen_vec)) * [0.0]
        for p in pen_vec:
            i = max(
                (i for i in range(len(orientations)) if number_of_usages[i] < self.r),
                key=lambda i: orientation_weights[i],
            )
            orientation_weights[i] -= 1.0
            number_of_usages[i] += 1
            yield AtomicStripBlueprint(orientations[i], penalty=p)
