import itertools
import math

import numpy as np

from pcpptc.utils import direction, turn_angle

from ...grid_instance import (
    PointBasedInstance,
    PointVertex,
    TouringCosts,
    VertexPassage,
)
from ...grid_solution import FractionalSolution


class DominantStripSelector:
    """
    Selects an orientation as the dominant atomic strip.
    Based on usage and the involved increased cost.
    """

    def __init__(self, exp=0.25, verbose=False):
        """
        epx: The remaining usage at 45deg extra cost
        """
        self.exp = exp
        self.verbose = verbose

    def __call__(self, orientations: list, usages: dict, tc: TouringCosts):
        weight = np.zeros(len(orientations))
        for vp, x in usages.items():

            def diff(o):
                a0 = turn_angle(
                    v0=vp.end_a, v1=vp.v, v2=vp.end_b, forced_orientation_at_v1=o
                )
                a1 = turn_angle(v0=vp.end_a, v1=vp.v, v2=vp.end_b)
                assert a0 >= a1 - 1e-5
                return a0 - a1

            min_diff = min(diff(o) for o in orientations)
            for i, o in enumerate(orientations):
                w = self.exp ** ((diff(o) - min_diff) / (0.25 * math.pi))
                weight[i] += x * w
        if self.verbose:
            print("Weights:", weight)
        return np.argmax(weight)


# %%

import typing

from ..atomic_strip_orientation.atomic_strip import AtomicStripBlueprint


class NeighborByUsage:
    def __call__(self, neighbors, usages: typing.Dict[VertexPassage, float]):
        neighbor_usages = np.zeros(len(neighbors))
        for vp, x in usages.items():
            for i, n in enumerate(neighbors):
                if n in vp.endpoints():
                    neighbor_usages[i] += x
        idx = [i for i in range(len(neighbors)) if neighbor_usages[i] > 0.02]
        idx.sort(key=lambda i: neighbor_usages[i], reverse=True)
        return idx


class NeighborsByMinMax:
    """
    Selects orientations by minimizing the worst case (actually squared cost but
    this is mainly for the case that we have multiple worst cases and then we want to
    lower as many as possible).
    """

    def _cost_matrix(
        self,
        vps: typing.List[VertexPassage],
        os: typing.List[float],
        touring_costs: TouringCosts,
    ):
        def costdiff(vp, o):
            c = touring_costs.vertex_passage_cost(vp)
            c_ = touring_costs.vertex_passage_cost(vp, forced_orientation=o)
            return c_ - c

        return np.array([[costdiff(vp, o) for o in os] for vp in vps])

    def __call__(self, vps, os, touring_costs, selected_idx):
        available_idx = [i for i, _ in enumerate(os) if i not in selected_idx]
        m = self._cost_matrix(vps, os, touring_costs)
        if selected_idx:
            vp_weights = m[:, selected_idx].min(axis=1) ** 2
        else:
            vp_weights = np.ones(len(vps))
        return min(available_idx, key=lambda i: m[:, i] @ vp_weights)


class NeighborBasedStripStrategy:
    def __init__(self, k: int, only_usage_based=False):
        self.k = k
        self.only_usage_based = only_usage_based
        self.dominant_strip_selector = DominantStripSelector()
        self.nbr_by_usage = NeighborByUsage()
        self.nbr_by_minmax = NeighborsByMinMax()

    def description(self) -> str:
        return (
            f"NeighborBasedStripStrategy selecting {self.k} atomic strips first on"
            " usage than on minimizing the worst case overhead."
        )

    def for_vertex(
        self,
        v: PointVertex,
        instance: PointBasedInstance,
        usages: typing.Dict[VertexPassage, float],
    ):
        nbrs = list(instance.graph.neighbors(v))
        value = instance.coverage_necessities[v].opportunity_loss(0.0)
        orientations = [direction(v.point, n) for n in nbrs]

        # Reduce orientations/atomic strips
        if len(orientations) > self.k or self.only_usage_based:
            # First by usage
            o_nbrs_idx = self.nbr_by_usage(nbrs, usages)[: self.k]
            # If this isn't enough, reduce the worst case
            vps = [
                VertexPassage(v, end_a=n0, end_b=n1)
                for n0, n1 in itertools.combinations_with_replacement(nbrs, 2)
            ]
            if not self.only_usage_based:
                while len(o_nbrs_idx) < self.k:
                    o_nbrs_idx.append(
                        self.nbr_by_minmax(
                            vps, orientations, instance.touring_costs, o_nbrs_idx
                        )
                    )
            # Filter the orientations
            orientations = [orientations[i] for i in o_nbrs_idx]

        # Select dominant one and create atomic strip blueprints
        if not orientations:
            return []
        dominant_i = self.dominant_strip_selector(
            orientations, usages, instance.touring_costs
        )
        return [
            AtomicStripBlueprint(o, 0.0 if i != dominant_i else value)
            for i, o in enumerate(orientations)
        ]

    def __call__(
        self, instance: PointBasedInstance, fractional_solution: FractionalSolution
    ) -> typing.Dict[PointVertex, typing.List[AtomicStripBlueprint]]:
        print("Using adaptive strip selection strategy.")
        return {
            v: self.for_vertex(v, instance, fractional_solution.at_vertex(v))
            for v in instance.graph.nodes
        }


# %%
