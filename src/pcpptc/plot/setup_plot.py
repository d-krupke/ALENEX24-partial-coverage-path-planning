import matplotlib.pyplot as plt


def setup_plot(figsize=(10, 10)):
    """
    Simply setups the plot. Nothing fancy.
    """
    plt.clf()
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal", adjustable="box")
    plt.tight_layout()
    return ax
