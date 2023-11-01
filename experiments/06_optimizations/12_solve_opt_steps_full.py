import datetime
import json
import os.path
import random
import sys




from aemeasure import Measurement, exists
from pcpptc import PolygonInstance
from pcpptc.grid_solver.cycle_cover.solver import CycleCoverSolverCallbacks
from pcpptc.grid_solver.grid_solver import GridSolverCallbacks
from pcpptc.solver_selection.abstract_solver import PolygonInstanceSolverCallbacks
from pcpptc.solver_selection.dmsh import MeshAlgorithm

# pool = Pool(8)

os.makedirs("./solutions_12/", exist_ok=True)


class Callbacks(PolygonInstanceSolverCallbacks):
    def __init__(self):
        super().__init__()

        class C(GridSolverCallbacks):
            def __init__(self):
                super().__init__()

                class D(CycleCoverSolverCallbacks):
                    def __init__(self):
                        self.lb = None

                    def on_fractional_solution(self, fractional_solution, objective):
                        self.lb = objective

                self.cc_callbacks = D()
                self.obj = None

            def on_grid_solution(self, tour, touring_cost, opportunity_loss):
                self.obj = touring_cost + opportunity_loss
                self.obj_tour = touring_cost
                self.obj_loss = opportunity_loss

        self.grid_callbacks = C()


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
    cb = Callbacks()
    solvers += [
        MeshAlgorithm(full_coverage=True, cc_opt_steps=k, t_opt_steps=0, callbacks=cb)
        for k in [0, 10, 25, 50, 100, 200]
    ]
    solvers += [
        MeshAlgorithm(full_coverage=True, cc_opt_steps=0, t_opt_steps=k, callbacks=cb)
        for k in [0, 10, 25, 50, 100, 200]
    ]

    instance_name = os.path.split(file_path)[-1].split(".")[0]
    solution_path = os.path.join("./solutions_12/", f"{instance_name}.results.json")
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
            m["integralization"] = solver.grid_solver.params.integralize
            m["cc_opt_steps"] = solver.grid_solver.params.cc_opt_steps
            m["t_opt_steps"] = solver.grid_solver.params.t_opt_steps
            m["turn_sum"] = solution.turn_angle_sum()
            m["instance"] = instance_name
            m["instance_path"] = file_path
            m["grid_lb"] = cb.grid_callbacks.cc_callbacks.lb
            m["grid_obj"] = cb.grid_callbacks.obj
            m["grid_obj_tour"] = cb.grid_callbacks.obj_tour
            m["grid_obj_loss"] = cb.grid_callbacks.obj_loss
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
