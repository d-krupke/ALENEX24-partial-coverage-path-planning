# %%
import random
import sys



from pcpptc.polygon_instance import RandomPolygonInstanceGenerator
from pcpptc.solver_selection.experimental import ExperimentalSolver

# %%
from pcpptc.solver_selection.simple_hexagonal import (
    RandomHexagonAlgorithm,
    RotatingHexagonAlgorithm,
)
from pcpptc.solver_selection.square import RandomSquareAlgorithm

tool_radius = 1.0
complexities = [2, 4, 8, 16]
sizes = [25, 30, 40]
holes = [1, 2, 4, 8, 16]
hole_sizes = [0.2, 0.4, 0.8, 1.6]
hole_complexities = [1, 2, 4]
turn_costs = [1.0, 5.0, 50.0]
combinations = [sizes, complexities, holes, hole_sizes, hole_complexities, turn_costs]

# %%


def random_instance(tries=0):
    if tries > 100:
        return RuntimeError("Could not generate instance. Check parameters")
    try:
        pi = RandomPolygonInstanceGenerator(
            complexity=random.choice(complexities),
            size=random.choice(sizes),
            turn_costs=random.choice(turn_costs),
            holes=random.choice(holes),
            hole_size=random.choice(hole_sizes),
            hole_complexity=random.choice(hole_complexities),
            tool_radius=tool_radius,
        )()

        return pi
    except AttributeError as ae:
        print(ae)
    except ValueError as ve:
        print(ve)
    return random_instance(tries + 1)


def run():
    pi = random_instance()
    x = random.randint(1, 1_000_000_000)
    pi.to_json(file_path=f"data/{x}.instance.json")
    print("Instance area", pi.feasible_area.area)
    alg_hex = RandomHexagonAlgorithm(full_coverage=True)
    alg_hexpb = RandomHexagonAlgorithm(full_coverage=True, point_based=True)
    alg_square = RandomSquareAlgorithm(full_coverage=True)
    alg_squarepb = RandomSquareAlgorithm(full_coverage=True, point_based=True)
    alg_rothex = RotatingHexagonAlgorithm(full_coverage=True)
    exp_solver = ExperimentalSolver()
    solution = exp_solver(pi)
    solution.to_json(f"data/{x}_exp.solution.json")
    solution = alg_rothex(pi)
    solution.to_json(f"data/{x}_rh.solution.json")
    for i in range(25):
        print(30 * "#")
        print("Try", i)
        print(30 * "#")
        print("### hexagonal")
        solution = alg_hex(pi)
        solution.to_json(f"data/{x}_hex{i}.solution.json")
        print("### square")
        solution = alg_square(pi)
        solution.to_json(f"data/{x}_square{i}.solution.json")
        print("### experimental")

        print("### hex pb")
        solution = alg_hexpb(pi)
        solution.to_json(f"data/{x}_hpb{i}.solution.json")
        print("### square pb")
        solution = alg_squarepb(pi)
        solution.to_json(f"data/{x}_spb{i}.solution.json")


for i in range(10):
    print(30 * "#")
    print("Experiment", i)
    print(30 * "#")
    run()
