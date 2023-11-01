"""
Prepares the data for 01_evaluation.ipynb on the integralization experiments.
"""

# %%

import os

# %%
import sys

import pandas as pd
from aemeasure import read_as_pd


from pcpptc import PolygonInstance, Solution

tables = []
for f in os.listdir("./solutions_01"):
    if not f.endswith(".results.json"):
        continue
    f = os.path.join("./solutions_01", f)
    tables.append(read_as_pd(f, verbose=False))

data = pd.concat(tables, ignore_index=True)
data.groupby(["solver"])["instance"].nunique()

# %%

data.drop_duplicates(subset=["instance", "solver"], inplace=True)


print("Loaded results for", data.groupby(["solver"])["instance"].nunique(), "instances")

# %%


data["point_based"] = data["solver"].apply(lambda s: "pb=True" in s)
# data = data[(data["t_opt_steps"]==0) & (data["cc_opt_steps"]==0)]
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

t_ = data.groupby("instance")[["touring_cost"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_cost"] = 100 * ((data["touring_cost"] / data["touring_cost_min"]) - 1)
data["relative_coverage"] = 100 * data["coverage"] / data["area"]
data["type"] = data["solver"].apply(lambda s: s[0])

# %%

t_ = data.groupby("instance")[["Obj"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_obj"] = 100 * ((data["Obj"] / data["Obj_min"]) - 1)
data.to_json("./00c_prepared_data.json")
