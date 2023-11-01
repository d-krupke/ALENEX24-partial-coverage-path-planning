import math


class AtomicStripBlueprint:
    """
    Suggest an atomic strip including the corresponding penalty.
    """

    def __init__(self, orientation: float, penalty: float):
        self.orientation = orientation % math.pi
        self.penalty = penalty
        assert self.penalty >= 0, "Penalty should not be negative."

    def is_skippable(self) -> bool:
        """
        True if it needs a skipping edge.
        """
        return self.penalty != math.inf

    def has_penalty(self) -> bool:
        """
        True if it cannot be skipped for free.
        """
        return self.penalty > 0.0

    def __str__(self):
        return f"AtomicStrip[{id(self)}]({self.orientation}, penalty={self.penalty})"

    def __repr__(self):
        return str(self)
