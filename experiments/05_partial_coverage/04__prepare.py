# %%

import os

import pandas as pd
from aemeasure import read_as_pd

# %%
from pcpptc import PolygonInstance, Solution

tables = []
for f in os.listdir("./solutions2"):
    if not f.endswith(".results.json"):
        continue
    f = os.path.join("./solutions2", f)
    tables.append(read_as_pd(f))

data = pd.concat(tables, ignore_index=True)
data.groupby(["solver"])["instance"].nunique()

# %%

print(data[data.isna().any(axis=1)])

# %%

data.dropna(inplace=True)
data = data[data["solver"] != "MeshAlgorithm(0.95)"]
data.groupby(["solver"])["instance"].nunique()

# %%



def rename(s):
    names = {
        "RotatingHexagonalAlgorithm(RotatingRegularHexagonal(full_coverage=False, point_based=False, with_boundary=False))": "Regular (Partial)",
        "RotatingHexagonalAlgorithm(RotatingRegularHexagonal(full_coverage=True, point_based=False, with_boundary=False))": "Regular (Full)",
        "RotatingHexagonalAlgorithm(RotatingRegularHexagonal(full_coverage=True, point_based=True, with_boundary=False))": "Regular (Full, PB)",
        "MeshAlgorithm(0.95, full_coverage=False)": "Mesh (Partial)",
        "MeshAlgorithm(0.95, full_coverage=True)": "Mesh (Full)",
    }
    return names.get(s, s)


data["solver"] = data["solver"].apply(rename)
data = data[data["solver"] != "Regular (Full, PB)"]

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

t_ = data.groupby("instance")[["touring_cost"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_cost"] = 100 * ((data["touring_cost"] / data["touring_cost_min"]) - 1)
data["relative_coverage"] = 100 * data["coverage"] / data["area"]
data["type"] = data["solver"].apply(lambda s: s[0])

# %%

t_ = data.groupby("instance")[["Obj"]].min()
data = data.merge(t_, left_on="instance", right_index=True, suffixes=("", "_min"))
data["relative_obj"] = 100 * ((data["Obj"] / data["Obj_min"]) - 1)
data.to_json("04_data.json")
