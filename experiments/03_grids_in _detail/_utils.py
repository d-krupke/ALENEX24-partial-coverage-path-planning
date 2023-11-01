import typing

import pandas as pd
from bisect import bisect
import matplotlib.pyplot as plt

import seaborn as sns
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

def convert_to_interval_on_values(table: pd.DataFrame, on_column: str, interval,
                                  values) -> pd.DataFrame:
    data = {c: [] for c in table.columns}
    for i, row in table.iterrows():
        lb, ub = interval(row[on_column])
        i_ = bisect(values, lb)
        for v in values[i_:]:
            if v > ub:
                break
            for c in table.columns:
                if c == on_column:
                    data[c].append(v)
                else:
                    data[c].append(row[c])
    return pd.DataFrame(data)


def convert_to_interval(table: pd.DataFrame,
                        on_column: str,
                        interval,
                        round_: typing.Callable[[float], float] = lambda x: x) \
        -> pd.DataFrame:
    values = []

    for v in table[on_column].unique():
        lb, ub = interval(v)
        values.append(round_(lb))
        values.append(round_(ub))
    values = list(set(values))
    values.sort()

    return convert_to_interval_on_values(table, on_column, interval, values)


def convert_to_percentage_interval(table: pd.DataFrame,
                                   on_column: str,
                                   percentage,
                                   round_: typing.Callable[[float], float] = lambda x: x
                                   ) -> pd.DataFrame:
    """
    A helpful function to convert the x-axis to +/- P% intervals. This is necessary
    if your x-values are sparse such that no aggregation can be performed.

    Depending on the values, the size of the table can strongly increase making it
    terribly slow. Use the 'round_' parameter to specify a desired resolution.
    This also allows a logarithmic resolution.
    :param table: The table containing the data
    :param on_column: Will be performed on this column (x-axis)
    :param percentage: The percentage to +/-
    :param round_: A function to reduce the resolution and increase the processing speed.
    :return:
    """
    def interval(v):
        d = (percentage / 100) * v
        return round_(v - d), round_(v + d)

    return convert_to_interval(table, on_column, interval, round_)