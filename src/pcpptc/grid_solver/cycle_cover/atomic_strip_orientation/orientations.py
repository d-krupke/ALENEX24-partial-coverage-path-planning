import math
import typing

from pcpptc.utils import direction

from ...grid_instance import PointBasedInstance, PointVertex


class NeighborOrientations:
    def __init__(self, instance: PointBasedInstance):
        self.instance = instance

    def __call__(self, v: PointVertex) -> typing.Iterator[float]:
        for n in self.instance.graph.neighbors(v):
            yield direction(n.point, origin=v.point)


class StepwiseOrientations:
    def __init__(self, n: int):
        self.n = n
        self.angle = math.pi / n

    def __call__(self) -> typing.Iterator[float]:
        for i in range(self.n):
            yield i * self.angle
