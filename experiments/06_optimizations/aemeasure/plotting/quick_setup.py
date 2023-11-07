import seaborn as sns
import matplotlib.pyplot as plt


def quick_plot_setup(use_tex=True) -> None:
    """
    Applies a quick setup for publication ready plots.
    This style has been used for LIPICs. Maybe other template need different styles.
    :return: None
    """
    sns.set_theme()
    plt.rcParams.update({
        "text.usetex": use_tex,
        "font.family": "serif",
        "font.serif": ["Helvetica"]})
