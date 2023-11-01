import datetime
import os.path
import random
import sys


from aemeasure import Measurement, exists
from pcpptc import PolygonInstance
from pcpptc.solver_selection.dmsh import MeshAlgorithm

# pool = Pool(8)

os.makedirs("./solutions_04/", exist_ok=True)


def solve(d):
    file_path, i = d
    print(file_path, i)
    start = datetime.datetime.now()
    instance = PolygonInstance.from_json(file_path=file_path)
    solvers = []
    # First round
    solvers += [
        MeshAlgorithm(
            full_coverage=False, integralization=inti, cc_opt_steps=0, t_opt_steps=0
        )
        for inti in [0, 10, 25, 50, 100, 200, 500]
    ]

    instance_name = os.path.split(file_path)[-1].split(".")[0]
    solution_path = os.path.join("./solutions_04/", f"{instance_name}.results.json")

    for i, solver in enumerate(solvers):
        if exists(
            solution_path, {"instance": instance_name, "solver": solver.identifier()}
        ):
            print("Skip", instance_name, i)
            continue
        with Measurement(solution_path) as m:
            solution = solver(instance)
            m["solution"] = solution.to_json(as_string=False)
            m["coverage"] = (
                instance.compute_covering_area(solution).area if solution else 0.0
            )
            m["touring_cost"] = instance.compute_touring_cost(solution)
            m["length"] = solution.euclidean_length()
            m["integralization"] = solver.grid_solver.params.integralize
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


instance_dir = "../05_partical_coverage/instances2"
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
