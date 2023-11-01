"""
This module optimizes the orientations of the atomic strips. For simple full coverage,
this is reasonably simple as only a dominant strip, that has to be covered, and the others
have to be found. For the generalized variant, every atomic strip actually gets a penalty
from the coverage necessity vector.
"""

from .adaptive import NeighborBasedStripStrategy
from .algorithm import EquiangularRepetitionAtomicStrips

__all__ = ["EquiangularRepetitionAtomicStrips", "NeighborBasedStripStrategy"]
