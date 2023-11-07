"""
Provide some simple functions for printing the context.
"""

import os
import sys
import typing
from datetime import datetime


def print_readme(line_limit: typing.Optional[int] = None):
    if not os.path.exists("./README.md"):
        print("No README.md")
        return
    with open("./README.md", "r") as f:
        for i, l in enumerate(f.readlines()):
            if line_limit and i == l:
                return
            print(l.rstrip())


def print_context():
    print("CWD:", os.getcwd())
    print("ARGV:", sys.argv)
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
