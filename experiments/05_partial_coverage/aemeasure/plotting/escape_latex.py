"""
Adapted from PyLatex (c) 2014 by Jelte Fennema, MIT-License
https://github.com/JelteF/PyLaTeX/blob/v1.3.2/pylatex/utils.py#L68-L100
"""
import numpy as np
import pandas as pd

_latex_special_chars = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '\n': '\\newline%\n',
    '-': r'{-}',
    '\xA0': '~',  # Non-breaking space
    '[': r'{[}',
    ']': r'{]}',
}


def escape_latex(s: str) -> str:
    """
    Escapes a string to be valid latex. Possibly necessary for using the quick-setup which
    applies latex to the column names.
    :param s: The string with potentially bad symbols
    :return: A string that can be compiled by latex
    """
    return ''.join(_latex_special_chars.get(c, c) for c in str(s))


def escape_latex_in_dataframe(df: pd.DataFrame, only_column_names=False):
    """
    Escapes the strings in a whole dataframe.
    WARNING: Potentially very slow!
    :param only_column_names: Only apply to column names.
    :param df:
    :return:
    """

    def escape(v):
        if type(v) is str:
            return escape_latex(v)
        else:
            return v

    if only_column_names:
        df = df.copy()
        df.columns = [escape(c) for c in df.columns]
        return df
    df = df.apply(np.vectorize(escape))
    df.columns = [escape(c) for c in df.columns]
    return df


