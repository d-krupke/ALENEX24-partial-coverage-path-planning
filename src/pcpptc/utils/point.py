import numpy as np
import shapely.geometry as sly


class Point:
    """
    A simple point_vertex data structure that should be compatible with most others.
    """

    def __init__(self, *args, **kwargs):
        if args:
            if len(args) == 1:
                try:
                    self._x = args[0][0]
                    self._y = args[0][1]
                except (KeyError, TypeError):
                    self._x = args[0].x
                    self._y = args[0].y
            elif len(args) == 2:
                self._x = args[0]
                self._y = args[1]
            else:
                msg = f"Don't know how to create a point from {args}"
                raise ValueError(msg)
        elif kwargs:
            self._x = kwargs["x"]
            self._y = kwargs["y"]
        self._x = float(self._x)
        self._y = float(self._y)
        assert isinstance(self._x, float)
        assert isinstance(self._y, float)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __len__(self):
        return 2

    def __getitem__(self, item):
        if item == 0 or item == "x":
            return self.x
        elif item == 1 or item == "y":
            return self.y
        msg = f"Bad access: {item}"
        raise KeyError(msg)

    def to_np(self) -> np.array:
        return np.array([self.x, self.y])

    def to_shapely(self) -> sly.Point:
        return sly.Point(self.x, self.y)

    def __add__(self, other):
        a = self.to_np() + other.to_np()
        return Point(a)

    def __mul__(self, other):
        a = other * self.to_np()
        return Point(a)

    def __sub__(self, p2):
        return Point(self.x - p2.x, self.y - p2.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __lt__(self, other):
        return hash(self) < hash(other)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __rmul__(self, other):
        return self * other


def distance(p0, p1):
    """
    Returns the euclidean distance between two waypoints.
    """
    return np.math.sqrt((p0.x - p1.x) ** 2 + (p0.y - p1.y) ** 2)
