import skgeom as sg
from optimizer import utils


def convert_skgeom_point(p: sg.Point2) -> utils.Point:
    x = p.x()
    y = p.y()
    return utils.Point(float(x), float(y))
