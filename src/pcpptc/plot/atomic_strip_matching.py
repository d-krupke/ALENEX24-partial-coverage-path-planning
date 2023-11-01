import matplotlib.pyplot as plt

from ..grid_solver.cycle_cover.atomic_strip_matcher import AtomicStripMatching
from .intermediate import plot_fractional_solution


def plot_atomic_strip_matching(ax: plt.Axes, asm: AtomicStripMatching, color="black"):
    fractional_solution = asm.to_solution()
    plot_fractional_solution(ax, fractional_solution, color=color)
