import datetime
import json
import os.path
import random
import sys


from aemeasure import Measurement, exists
from pcpptc import PolygonInstance
from pcpptc.solver_selection.dmsh import MeshAlgorithm
from pcpptc.solver_selection.simple_hexagonal import (
    RotatingHexagonAlgorithm,
)

# pool = Pool(8)

os.makedirs("./solutions2/", exist_ok=True)


def clean_json(path):
    if not os.path.exists(path):
        return
    entries = []
    clean = False
    with open(path) as f:
        data = json.load(f)
        for e in data:
            if not e:
                clean = True
                continue
            if " object at " in e["solver"]:
                print("clean", e, "in", path)
                clean = True
                continue
            entries.append(e)
    if clean:
        with open(path, "w") as f:
            json.dump(entries, f)


def solve(d):
    file_path, i = d
    print(file_path, i)
    start = datetime.datetime.now()
    instance = PolygonInstance.from_json(file_path=file_path)
    solvers = []
    # First round
    solvers += [MeshAlgorithm(full_coverage=fc) for fc in [True, False]]
    solvers += [RotatingHexagonAlgorithm(full_coverage=fc) for fc in [True, False]]
    solvers += [
        RotatingHexagonAlgorithm(full_coverage=fc, point_based=True) for fc in [True]
    ]

    instance_name = os.path.split(file_path)[-1].split(".")[0]
    solution_path = os.path.join("./solutions2/", f"{instance_name}.results.json")
    clean_json(solution_path)

    for i, solver in enumerate(solvers):
        if exists(
            solution_path, {"instance": instance_name, "solver": solver.identifier()}
        ):
            print("Skip", instance_name, i)
            continue
        with Measurement(solution_path) as m:
            solution = solver(instance)
            m["solution"] = solution.to_json(as_string=False)
            m["coverage"] = instance.compute_covering_area(solution).area
            m["touring_cost"] = instance.compute_touring_cost(solution)
            m["length"] = solution.euclidean_length()
            m["turn_sum"] = solution.turn_angle_sum()
            m["instance"] = instance_name
            m["instance_path"] = file_path
            m.save_metadata()
            m.save_seconds()
            m["solver"] = solver.identifier()
            m["i"] = i
            m["turn_factor"] = instance.turn_cost
    time = datetime.datetime.now() - start
    print("NEEDED TIME:", i, time)


instance_dir = "./instances2"
instances = []
i = 0
for f in os.listdir(instance_dir):
    if "instance.json" not in f:
        continue
    f = os.path.join(instance_dir, f)
    instances.append((f, i))
    i += 1

random.shuffle(instances)
for x in instances:
    print(x)
    solve(x)

# pool.map(solve, instances)
