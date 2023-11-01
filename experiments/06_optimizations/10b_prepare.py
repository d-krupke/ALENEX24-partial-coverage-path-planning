# %%


# %%

import os

# %%
import sys

import pandas as pd
from aemeasure import read_as_pd


from pcpptc import PolygonInstance, Solution

# %%


tables = []
for f in os.listdir("./solutions_10"):
    if not f.endswith(".results.json"):
        continue
    f = os.path.join("./solutions_10", f)
    tables.append(read_as_pd(f))

data = pd.concat(tables, ignore_index=True)
data.groupby(["solver"])["instance"].nunique()

# %%


# data.dropna(inplace=True)
data.drop_duplicates(subset=["instance", "solver"], inplace=True)
data.groupby(["solver"])["instance"].nunique()

# %%



# %%


# %%

data["type"] = data["solver"].apply(lambda s: "hex" if "Hex" in s else "square")
data["point_based"] = data["solver"].apply(lambda s: "pb=True" in s)

# %%


# %%

instance_paths = list(data["instance_path"].unique())
instances = {f: PolygonInstance.from_json(file_path=f) for f in instance_paths}
instance_areas = pd.DataFrame(
    data={"area": [i.original_area.area for i in instances.values()]},
    index=instance_paths,
)
data = data.merge(instance_areas, left_on="instance_path", right_index=True)


def compute_objective(row):
    instance = instances[row["instance_path"]]
    solution = Solution.from_json(data=row["solution"])
    instance: PolygonInstance
    return instance.compute_touring_cost(
        solution.waypoints
    ) + instance.compute_missed_covering_value(solution.waypoints)


data["Obj"] = data.apply(compute_objective, axis=1)

# %%

# data.drop(["solution"], inplace=True, axis=1)

# %%

t_ = data.groupby("instance")[["touring_cost"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_cost"] = 100 * ((data["touring_cost"] / data["touring_cost_min"]) - 1)
data["relative_coverage"] = 100 * data["coverage"] / data["area"]
data["type"] = data["solver"].apply(lambda s: s[0])

# %%

t_ = data.groupby("instance")[["Obj"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_obj"] = 100 * ((data["Obj"] / data["Obj_min"]) - 1)

obj_without = data[(data["cc_opt_steps"] == 0) & (data["t_opt_steps"] == 0)][
    ["instance", "Obj", "grid_obj"]
]
obj_without.rename(columns={"Obj": "pobj_wo", "grid_obj": "gobj_wo"}, inplace=True)
data = data.merge(right=obj_without, left_on="instance", right_on="instance")

data["gobj_change"] = 100 * (data["grid_obj"] / data["gobj_wo"] - 1)
data["gobj_opt_gap"] = 100 * (data["grid_obj"] / data["grid_lb"] - 1)
data["pobj_change"] = 100 * (data["Obj"] / data["pobj_wo"] - 1)

data.to_json("10c_prepared_data.json")
