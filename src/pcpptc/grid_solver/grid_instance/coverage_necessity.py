import math


class CoverageNecessity:
    """
    Defines the necessity for a point to be covered resp. the penalty for skipping it.
    It is possible to require the first coverage and making a second optional via a
    penalty. You can not limit the number of coverages. Just increase it either hard
    or with penalties.
    Note that the computational costs can increase drastically with multiple such
    constraints per vertex because this may also require other waypoints to be visited
    multiple times. The problem grows linear with the maximum number of such
    constraints at a vertex (we have to increase the capacity for all other waypoints too).
    """

    def __init__(self, penalty_vector):
        self.penalty_vector = penalty_vector
        assert not penalty_vector or penalty_vector[0] > 0, "Should always be >0"
        assert penalty_vector == sorted(
            penalty_vector, reverse=True
        ), "Should be decreasing"
        self._verify_vec()

    def __len__(self):
        return len(self.penalty_vector)

    def _verify_vec(self):
        for i in range(len(self.penalty_vector) - 1):
            if self.penalty_vector[i] < self.penalty_vector[i + 1]:
                msg = "Penalties are not allow to increase."
                raise ValueError(msg)

    def number_of_necessary_coverages(self) -> int:
        return len([p for p in self.penalty_vector if p == math.inf])

    def penalty_for_skipping_the_ith_coverage(self, i: int):
        if i < len(self):
            return self.penalty_vector[i]
        else:
            return 0.0

    def opportunity_loss(self, coverage):
        i = 0
        value = 0.0
        while coverage - i > 0 and i < len(self.penalty_vector):
            value += self.penalty_vector[i] * min(coverage - i, 1)
            i += 1
        assert value >= 0.0
        return sum(self.penalty_vector) - value


class OptionalCoverage(CoverageNecessity):
    """
    Defines a coverage that can be skipped for free.
    """

    def __init__(self):
        super().__init__([])


class SimpleCoverage(CoverageNecessity):
    """
    Defines a constraint of a simple, single coverage.
    """

    def __init__(self):
        super().__init__([math.inf])


class MultiCoverage(CoverageNecessity):
    """
    Defines a constraint to cover a point number_of_different_orientations times.
    """

    def __init__(self, k: int):
        assert k >= 0
        super().__init__(k * [math.inf])


class PenaltyCoverage(CoverageNecessity):
    """
    Defines a constraint that allows skipping a point for a penalty.
    """

    def __init__(self, penalty: float):
        assert penalty >= 0
        if penalty == 0:
            super().__init__([])
        else:
            super().__init__([penalty])


class CoverageNecessities:
    def __init__(self, default=SimpleCoverage()):
        self.default = default
        self._data = {}

    def __getitem__(self, item):
        return self._data.get(item, self.default)

    def __setitem__(self, key, value):
        self._data[key] = value
