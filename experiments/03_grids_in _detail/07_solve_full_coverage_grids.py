import datetime
import json
import os.path
import random
import sys


from aemeasure import Measurement, exists
from pcpptc import PolygonInstance
from pcpptc.solver_selection.dmsh import DmshAlgorithm, GmshAlgorithm

# pool = Pool(8)

os.makedirs("./solutions/", exist_ok=True)


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
    solvers += [DmshAlgorithm(full_coverage=True, point_based=False, hard_corners=True)]
    solvers += [
        DmshAlgorithm(
            full_coverage=True, point_based=False, hard_corners=True, scale=1.0
        )
    ]
    solvers += [
        DmshAlgorithm(
            full_coverage=True, point_based=False, hard_corners=True, scale=0.9
        )
    ]
    solvers += [
        GmshAlgorithm(
            full_coverage=True, point_based=False, hard_corners=True, alg=i, quad=False
        )
        for i in [1, 6, 8, 9]
    ]
    solvers += [
        GmshAlgorithm(
            full_coverage=True,
            point_based=False,
            hard_corners=True,
            alg=i,
            quad=False,
            scale=0.95,
        )
        for i in [9]
    ]
    solvers += [
        GmshAlgorithm(
            full_coverage=True,
            point_based=False,
            hard_corners=True,
            alg=i,
            quad=False,
            scale=0.9,
        )
        for i in [9]
    ]
    solvers += [
        GmshAlgorithm(
            full_coverage=True, point_based=False, hard_corners=True, quad=True, alg=i
        )
        for i in [8, 9]
    ]

    instance_name = os.path.split(file_path)[-1].split(".")[0]
    solution_path = os.path.join("./solutions/", f"{instance_name}.results.json")
    clean_json(solution_path)

    for i, solver in enumerate(solvers):
        if exists(
            solution_path, {"instance": instance_name, "solver": solver.identifier()}
        ):
            print("Skip", instance_name, i)
            continue
        with Measurement(solution_path) as m:
            try:
                solution = solver(instance)
                m["solution"] = solution.to_json(as_string=False)
                m["coverage"] = instance.compute_covering_area(solution).area
                m["touring_cost"] = instance.compute_touring_cost(solution)
                m["length"] = solution.euclidean_length()
                m["turn_sum"] = solution.turn_angle_sum()
            except AssertionError as ae:
                if str(ae) != "Exceeded maximum number of boundary steps.":
                    raise ae
                else:
                    print(ae)
            m["instance"] = instance_name
            m["instance_path"] = file_path
            m.save_metadata()
            m.save_seconds()
            m["solver"] = solver.identifier()
            m["i"] = i
            m["turn_factor"] = instance.turn_cost
    time = datetime.datetime.now() - start
    print("NEEDED TIME:", i, time)


instance_dir = "../01_grid/instances"
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
    if (
        "/77." in x[0]
    ):  # this instance becomes disconnected by the polygon processing. Probably too close holes.
        continue
    solve(x)

# pool.map(solve, instances)
