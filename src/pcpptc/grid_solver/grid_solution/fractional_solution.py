import typing
from collections import defaultdict

from ..grid_instance.point import PointVertex
from ..grid_instance.vertex_passage import VertexPassage


class FractionalSolution:
    """
    Represents the solution for a graph from the fractional linear program.
    Because the values are probably coming from Gurobi and hence have slight deviations,
    an epsilon is used to determine if a value is zero or if two values are equal.
    """

    # The epsilon, values are allowed to differ to still be considered equal.
    eps = 0.001

    def __init__(self):
        self._usages = {}
        self._at_vertex = defaultdict(set)

    def __setitem__(self, vp: VertexPassage, value: float):
        """
        Sets the usages of a passage.
        """
        assert -self.eps <= value
        if value <= self.eps and vp in self._usages:
            self._usages.pop(vp)
        else:
            self._usages[vp] = value
            self._at_vertex[vp.v].add(vp)

    def add(self, vp: VertexPassage, value: float = 1.0):
        """
        Adds the value to the possibly already existing usage of the passage.
        """
        assert isinstance(vp, VertexPassage)
        self._usages[vp] = self._usages.get(vp, 0.0) + value
        self._at_vertex[vp.v].add(vp)

    def __getitem__(self, vp: VertexPassage) -> float:
        """
        Returns the sum of vertex passages.
        """
        return self._usages.get(vp, 0.0)

    def at_vertex(self, pv: PointVertex):
        return {k: self[k] for k in self._at_vertex[pv]}
        # return {k: x for k, x in self if k.v == pv}

    def coverage(self, v: PointVertex):
        return sum(x for k, x in self.at_vertex(v).items())

    def vertices(self) -> typing.List[PointVertex]:
        return list({vp.v for vp, x in self})

    def __iter__(self) -> typing.Iterable[typing.Tuple[VertexPassage, float]]:
        """
        Iterates over all non-zero vertex passages.
        """
        yield from self._usages.items()

    def __eq__(self, other):
        for k, v in self:
            if abs(v - other[k]) > self.eps:
                return False
        return all(abs(v - self[k]) <= self.eps for k, v in other)

    def __contains__(self, item):
        return item in self._usages and self._usages[item] > 0.0

    def __add__(self, other: "FractionalSolution") -> "FractionalSolution":
        fs = FractionalSolution()
        for vp, x in self:
            fs.add(vp, x)
        for vp, x in other:
            fs.add(vp, x)
        return fs

    def __sub__(self, other):
        fs = FractionalSolution()
        for vp, x in self:
            if x - other[vp] > 0:
                fs[vp] = x - other[vp]
        return fs

    def angle_sum(self) -> float:
        """
        Return the sum of turn angles of the solution.
        """
        s = 0.0
        for vp, x in self:
            s += vp.turn_angle() * x
        return s

    def length(self) -> float:
        """
        Returns the length of the solution
        """
        s = 0.0
        for vp, x in self:
            s += 0.5 * vp.distance() * x
        return s

    def is_integral(self, eps=0.01):
        return all(abs(round(val) - val) <= eps for vp, val in self)
