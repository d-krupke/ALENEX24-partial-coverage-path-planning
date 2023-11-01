
from pcpptc.utils import Point


class PointVertex:
    """
    Representing a point vertex in an embedded graph.
    The primary difference to a point is that it has a unique id used for hashing and
    comparison. This allows it to change its position without invalidating dictionaries
    and such.
    """

    def __init__(self, *args, **kwargs):
        self.point = Point(*args, **kwargs)

    @property
    def x(self):
        return self.point.x

    @property
    def y(self):
        return self.point.y

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

    def __lt__(self, other):
        return hash(self) < hash(other)

    def __getitem__(self, item):
        if item == 0 or item == "x":
            return self.x
        elif item == 1 or item == "y":
            return self.y
        msg = f"Bad access: {item}"
        raise KeyError(msg)

    def __str__(self):
        return f"PointVertex[{id(self)}]@({self.x}, {self.y})"

    def __repr__(self):
        return str(self)
