"""
Prepares the data for 01_evaluation.ipynb on the integralization experiments.
"""

# %%

# %%
import sys

import pandas as pd


from pcpptc import PolygonInstance

data = pd.read_json("./00c_prepared_data.json")
# %%

data.drop_duplicates(subset=["instance", "solver"], inplace=True)


def extract_toptsteps(row):
    for s in row["solver"].split(","):
        if "t_opt_steps=" in s:
            return int(s.split("=")[1])
    raise AssertionError()


data["t_opt_steps"] = data.apply(extract_toptsteps, axis=1)


def extract_toptsize(row):
    for s in row["solver"].split(","):
        if "t_opt_size=" in s:
            return int(s.split("=")[1])
    raise AssertionError()


data["t_opt_size"] = data.apply(extract_toptsize, axis=1)


def extract_ccptsteps(row):
    for s in row["solver"].split(","):
        if "cc_opt_steps=" in s:
            return int(s.split("=")[1])
    raise AssertionError()


data["cc_opt_steps"] = data.apply(extract_ccptsteps, axis=1)


def is_default(row):
    default = {
        "integralization": 50,
        "t_opt_steps": 25,
        "cc_opt_steps": 25,
        "t_opt_size": 50,
    }
    return all(row[k] == v for k, v in default.items())


data = data[data.apply(is_default, axis=1)]

instance_paths = list(data["instance_path"].unique())
instances = {f: PolygonInstance.from_json(file_path=f) for f in instance_paths}
instance_areas = pd.DataFrame(
    data={"area": [i.original_area.area for i in instances.values()]},
    index=instance_paths,
)
data = data.merge(instance_areas, left_on="instance_path", right_index=True)

# %%

data["grid_opt_gap"] = ((data["grid_obj"] / data["grid_lb"]) - 1) * 100
data["obj_gap"] = data["Obj"] / data["grid_obj"]
# %%


def compute_value_sum(row):
    instance = instances[row["instance_path"]]
    value = sum(a.area * v for a, v in instance.valuable_areas)
    return value


data["value_sum"] = data.apply(compute_value_sum, axis=1)
# %%


def compute_value_density(row):
    instance = instances[row["instance_path"]]
    value = sum(a.area * v for a, v in instance.valuable_areas)
    return value / instance.original_area.area


data["value_density"] = data.apply(compute_value_density, axis=1)
print("Loaded results for", data.groupby(["solver"])["instance"].nunique(), "instances")

# %%
data.to_json("./06c_prepared_data.json")
