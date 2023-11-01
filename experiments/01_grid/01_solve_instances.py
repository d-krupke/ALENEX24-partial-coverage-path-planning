import datetime
import json
import os.path
import random
import sys


from aemeasure import Measurement, exists
from pcpptc import PolygonInstance
from pcpptc.solver_selection.simple_hexagonal import (
    RandomHexagonAlgorithm,
    RotatingHexagonAlgorithm,
)
from pcpptc.solver_selection.square import (
    RandomSquareAlgorithm,
    RotatingSquareAlgorithm,
)

# pool = Pool(8)

os.makedirs("./solutions_02/", exist_ok=True)


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
    repetitions = 10
    solvers = []
    # First round
    solvers += repetitions * [RandomHexagonAlgorithm(full_coverage=True)]
    solvers += repetitions * [
        RandomHexagonAlgorithm(full_coverage=True, point_based=True)
    ]
    solvers += repetitions * [RandomSquareAlgorithm(full_coverage=True)]
    solvers += repetitions * [
        RandomSquareAlgorithm(full_coverage=True, point_based=True)
    ]
    solvers += [RotatingHexagonAlgorithm(full_coverage=True)]
    solvers += [RotatingHexagonAlgorithm(full_coverage=True, point_based=True)]
    solvers += [RotatingSquareAlgorithm(full_coverage=True, point_based=True)]
    solvers += [RotatingSquareAlgorithm(full_coverage=True)]

    # Second round
    solvers += repetitions * [RandomHexagonAlgorithm(full_coverage=True)]
    solvers += repetitions * [
        RandomHexagonAlgorithm(full_coverage=True, point_based=True)
    ]
    solvers += repetitions * [RandomSquareAlgorithm(full_coverage=True)]
    solvers += repetitions * [
        RandomSquareAlgorithm(full_coverage=True, point_based=True)
    ]
    solvers += (
        2 * repetitions * [RandomSquareAlgorithm(full_coverage=True, point_based=True)]
    )
    solvers += (
        2 * repetitions * [RandomHexagonAlgorithm(full_coverage=True, point_based=True)]
    )
    solvers += [RotatingSquareAlgorithm(full_coverage=True, point_based=True)]
    instance_name = os.path.split(file_path)[-1].split(".")[0]
    solution_path = os.path.join("./solutions_02/", f"{instance_name}.results.json")
    clean_json(solution_path)

    for i, solver in enumerate(solvers):
        if exists(solution_path, {"instance": instance_name, "i": i}):
            print("Skip", instance_name, i)
            continue
        with Measurement(solution_path) as m:
            solution = solver(instance)
            m["instance"] = instance_name
            m["instance_path"] = file_path
            m.save_metadata()
            m.save_seconds()
            m["solver"] = solver.identifier()
            m["solution"] = solution.to_json(as_string=False)
            m["i"] = i
            m["coverage"] = instance.compute_covering_area(solution).area
            m["touring_cost"] = instance.compute_touring_cost(solution)
            m["length"] = solution.euclidean_length()
            m["turn_sum"] = solution.turn_angle_sum()
            m["turn_factor"] = instance.turn_cost
    time = datetime.datetime.now() - start
    print("NEEDED TIME:", i, time)


instance_dir = "./instances"
instances = []
i = 0
for f in os.listdir(instance_dir):
    if "instance.json" not in f:
        continue
    f = os.path.join(instance_dir, f)
    instances.append((f, i))
    i += 1

random.shuffle(instances)
bad_instances = []
for x in instances:
    try:
        solve(x)
    except json.decoder.JSONDecodeError as jsone:
        bad_instances.append(x)
        print("FAILED TO LOAD", x, "CONTINUE WITH OTHER INSTANCES")

if bad_instances:
    msg = f"Could not solve due to json error: {bad_instances}"
    raise Exception(msg)
# pool.map(solve, instances)
