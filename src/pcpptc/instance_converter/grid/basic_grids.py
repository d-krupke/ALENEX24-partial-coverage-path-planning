import math
import typing


def __frange(a, b, step):
    x = a
    while x <= b:
        yield x
        x += step


def hexagonal_grid(
    min_x: float, min_y: float, max_x: float, max_y: float, side_length: float = 1.0
) -> typing.Iterable[typing.Tuple[float, float]]:
    """
    Returns the waypoints of an hexagonal grid within the bounding box.
    The distance between adjacent waypoints is defined by `side_length`.
    The first point is (min_x, min_y).
    """
    r = 0
    y = min_y
    y_step_length = side_length * math.sqrt(3) / 2
    while y <= max_y:
        start_x = min_x if r % 2 == 0 else min_x + 0.5 * side_length
        for x in __frange(start_x, max_x, side_length):
            yield x, y
            x += side_length
        y += y_step_length
        r += 1


def square_grid(
    min_x: float, min_y: float, max_x: float, max_y: float, side_length: float = 1.0
) -> typing.Iterable[typing.Tuple[float, float]]:
    """
    Returns the waypoints of an square grid within the bounding box.
    The distance between adjacent waypoints is defined by `side_length`.
    The first point is (min_x, min_y).
    """
    for x in __frange(min_x, max_x, side_length):
        for y in __frange(min_y, max_y, side_length):
            yield x, y
