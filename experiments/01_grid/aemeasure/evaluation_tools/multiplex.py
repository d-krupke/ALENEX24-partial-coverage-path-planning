import math
from bisect import bisect

import pandas as pd
import typing


class Range:
    """
    A class to define available values for the multiplex aggregation.
    `stop` is exclusive, as expected in python.
    """

    def __init__(self, start: float, stop: float, step: float):
        self.start = start
        self.stop = stop
        self.step = step

    def subrange(self, start: float, stop: float) -> typing.Iterable[float]:
        if start < self.start:
            x = self.start
        else:
            steps = math.ceil((start - self.start) / self.step)
            x = self.start + steps * self.step
        while x < self.stop and x < stop:
            yield x
            x += self.step

    def __iter__(self) -> typing.Iterable[float]:
        x = self.start
        while x < self.stop:
            yield x
            x += self.step


def range_multiplex(table: pd.DataFrame,
                    to_column: str,
                    bounds: typing.Callable[[pd.Series], typing.Tuple[float, float]],
                    values: Range):
    """
    Duplicates rows to a range of values on a new column.
    This is useful for plotting and aggregating if the corresponding values are to sparse.
    For example if we want to plot over some x but nearly all x are different, the plot
    can become rather messy and unstable.
    See `percentage_multiple` for an example on +- percentage.
    parameters:
    table: the data table
    to_column: will write to this column
    bounds: a function that returns a lower and upper bound for each row
    values: a range of values that the new x can take.
    """
    data = {c: [] for c in table.columns}
    data[to_column] = []
    for i, row in table.iterrows():
        lb, ub = bounds(row)
        for x in values.subrange(lb, ub):
            for c in table.columns:
                data[c].append(row[c])
            data[to_column].append(x)
    return pd.DataFrame(data)


def percentage_multiplex(table: pd.DataFrame,
                         on_column: str,
                         to_column: str,
                         values: Range,
                         percentage: float) -> pd.DataFrame:
    """
    Helps to apply a row to a +- percentage interval for aggregation.
    """

    def bounds(row):
        x = row[on_column]
        p = (percentage / 100) * x
        return x - p, x + p

    return range_multiplex(table, to_column=to_column, bounds=bounds, values=values)



