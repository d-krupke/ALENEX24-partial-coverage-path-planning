import math
import typing


class EquiangularOrientationList:
    def __init__(self, k: int):
        self.k = k
        self.angle = math.pi / k

    def __call__(self, o) -> typing.List[float]:
        return [(o + i * self.angle) % math.pi for i in range(self.k)]
