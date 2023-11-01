import typing
from collections import defaultdict

from ..grid_instance import PointBasedInstance
from ..grid_solution import Cycle


def calculate_cycle_penalties(
    instance: PointBasedInstance, cc: typing.List[Cycle], substract_touring_costs=True
) -> typing.Dict[Cycle, float]:
    """
    This algorithm will accumulate the penalties of the vertices to the cycles.
    It will greedily assign the penalties to the first covering cycle_cover in the list, so
    the order is important.
    If a vertex has a penalty of [inf, inf], the first two cycles in the list that cover
    it will have the penalty 'inf'. If the first vertex covers it twice, only it will
    have a penalty of inf.
    If a vertex has a penalty of [10,5] and the first cycle_cover covers it twice, the cycle_cover
    will be assigned the penalty of 10+5 for this vertex (plus maybe further penalties
    of other vertices). If it only covers it once, it will only get a penalty of 10 for
    this vertex. The second vertex covering it, will get the remaining 5.
    """
    coverages = defaultdict(lambda: 0)
    cycle_penalties = {}
    for cycle in cc:
        if substract_touring_costs:
            vp_cost = instance.touring_costs.vertex_passage_cost
            touring_cost = sum(vp_cost(vp) for vp in cycle.passages)
            penalty = -touring_cost
        else:
            penalty = 0.0
        for v, usages in cycle.covered_vertices().items():
            v_penalties = instance.coverage_necessities[v].penalty_vector
            # take the next `usages` number of uncharged penalties
            for i in range(coverages[v], min(len(v_penalties), coverages[v] + usages)):
                penalty += v_penalties[i]
            coverages[v] += usages
        cycle_penalties[cycle] = penalty
    return cycle_penalties
