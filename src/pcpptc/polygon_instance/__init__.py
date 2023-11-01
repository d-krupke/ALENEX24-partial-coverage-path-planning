"""
This modules defines the underlying instances that should be as practical as possible
while still remaining clearly mathematical defined. While it is still a mathematical
optimization problem, it is not meant to be optimized directly because it is rather
expensive to evaluate. Instead it is rather used as a simulation.

Why do not directly use a simulation?
-> Because creating a proper realistic simulation is difficult. We consider a generic
    technique and there simply is no specific simulation we could use. Also, it would be
    not full transparent. The mathematical model on the other hand is absolutely
    transparent and generic. Also, it allows to model many scenarios and random polygon
    can easily be generated.

This module is based on shapely which itself is based on the C++ engine GEOS. It is
reasonably fast but geometric operations are intrinsically expensive. It is not
absolutely exact but the errors in the usage should be reasonably small, if instances
are not degenerated.

# How does an polygon look like?

First of all, we are given a polygon that specifies the reachable positions for a
circe-shaped tool (it position is defined by its center). If we have a room, this would
be the polygon of the room minus some offset with the length of the tool's radius.

Second, we have a factor for the distance and for the turn cost. For defining the cost of
moving one unit straight and turning one radian.

Third, we have a set of polygons with associated values for defining areas we want to
cover. The value equals the prize for covering one square unit of the corresponding
polygon resp. the opportunity loss of missing one square unit. These polygons are allowed
to overlap and in this case, the values are summed. The overlapping areas are computed
by computing the covered area of the tour and intersecting it with the corresponding
polygon. The round corners of the covered area are approximated by a set of segments.

Last, we have a set of polygons with associated cost multiplier. These define areas that
are expensive to cover or should be avoided (while still being allowed if it is a good
shortcut). The part of a tour that goes through such a polygon (measured by the center)
has an increased cost, corresponding to a factor of the cost multiplier (e.g., for 2, the
every turn and traveling is twice as expensive). If multiple such polygons overlap, the
costs are multiplied.

This allows us to define where and at which cost the tool can move. Also it allows us
to define which area we would want to cover at what price (like dirty areas a cleaning
robot should take care off based on the dirt level) and what areas to avoid (e.g. the
robot might have problems with some carpets that could be marked this way). Note that
these two areas do not have to be exclusive. There can be areas that we would like to
cover but that are expensive. This means, that it should only be used for covering and
not for simply passing through to another location.

# Shortcomings

We currently have only linear costs (traveling twice as long, costs twice as much) which
can only locally modified by the expensive areas. However, due to acceleration and other
reasons, this is not always accurate enough.

Another point is that most we only allow a discrete modelling of valuable and expensive
areas. In reality, we will most often have a density distribution. However, we can
approximate such a density distribution often reasonably well with a set of polygons.
Note that the polygons should remain sufficiently wide. Prefer overlapping larger polygons
to exclusive but smaller ones.
"""


from .instance import PolygonInstance
from .random_instance_generator import RandomPolygonInstanceGenerator
from .solution import Solution

__all__ = [
    "PolygonInstance",
    "Solution",
    "RandomPolygonInstanceGenerator",
]
