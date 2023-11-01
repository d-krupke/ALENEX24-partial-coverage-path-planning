# %%
import json.decoder
import os

import numpy as np
import pandas as pd
from aemeasure import read_as_pd
from pcpptc import PolygonInstance

path = "./solutions_02"
tables = []
for f in os.listdir(path):
    if not f.endswith(".results.json"):
        continue
    f = os.path.join(path, f)
    try:
        tables.append(read_as_pd(f))
    except json.decoder.JSONDecodeError as jsone:
        print(jsone)

data = pd.concat(tables, ignore_index=True)
data.dropna(inplace=True)

# %%


def get_point_distance(row):
    solution = row["solution"]
    waypoints = solution["waypoints"]
    p0 = np.array(waypoints[0])
    p1 = np.array(waypoints[1])
    return round(np.linalg.norm(p0 - p1), 3)


data["point_dist"] = data.apply(get_point_distance, axis=1)
print(data["point_dist"].unique())


def descr(row):
    solver = row["solver"]
    dist = row["point_dist"]
    if "hex" in solver.lower():
        type = "Triangular"
        if dist == 2.309:
            d = "Line-based"
        else:
            assert dist == 1.732
            d = "Point-based"
    elif "square" in solver.lower():
        type = "Square"
        if dist == 2:
            d = "Line-based"
        else:
            assert dist == 1.414
            d = "Point-based"
    else:
        msg = f"Could not detect type of {solver}"
        raise ValueError(msg)
    return f"{type}, {d}"
    if "pb=True" in solver or "point_based=True" in solver:
        d = "Point-based"
    elif "pb=False" in solver or "point_based=False" in solver:
        d = "Line-based"
    else:
        msg = f"Could not detect base of {solver}"
        raise ValueError(msg)
    return f"{type}, {d}"


data["Grid"] = data.apply(descr, axis=1)
data.dropna(inplace=True)

# %%

ts = []
for instance in data["instance"].unique():
    for grid in data["Grid"].unique():
        t = data[
            (data["instance"] == instance)
            & (data["Grid"] == grid)
            & data["solver"].str.contains("Rotating")
        ].copy()
        t["Orientation"] = "Optimized"
        ts.append(t.head(1))
        if t.empty:
            print("INCOMPLETE ROTATG", instance, grid)
        t = data[
            (data["instance"] == instance)
            & (data["Grid"] == grid)
            & ~data["solver"].str.contains("Rotating")
        ].copy()
        t["Orientation"] = "Random"
        ts.append(t.head(20))
        if len(t) < 20:
            print("INCOMPLETE", instance, grid, len(t))
data = pd.concat(ts)
print("Solver:", data["solver"].unique())
print(data["instance"].nunique(), "instances")
print(data.groupby(["Grid", "Orientation"])["instance"].count())
# %%


# %%

instance_paths = list(data["instance_path"].unique())
instances = [PolygonInstance.from_json(file_path=f) for f in instance_paths]
instance_areas = pd.DataFrame(
    data={"area": [i.original_area.area for i in instances]}, index=instance_paths
)
data = data.merge(instance_areas, left_on="instance_path", right_index=True)
data["relative_coverage"] = 100 * data["coverage"] / data["area"]
data.sort_values(by=["area"], inplace=True)

# %%

t_ = data.groupby("instance")[["touring_cost", "length", "turn_sum"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_cost"] = data["touring_cost"] / data["touring_cost_min"]
data["relative_length"] = data["length"] / data["length_min"]
data["relative_turn_sum"] = data["turn_sum"] / data["turn_sum_min"]
data.to_json("01c_data.json")

"""

t_ = data.groupby(["instance", "Grid"])[["touring_cost"]].min()
def is_min(row):
    return t_.loc[(row["instance"], row["Grid"])]["touring_cost"]==row["touring_cost"]
data = data[data[["instance", "Grid", "touring_cost"]].apply(is_min , axis=1)]
"""
