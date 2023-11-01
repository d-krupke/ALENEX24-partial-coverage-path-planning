def show_solver_diffs(data):
    diffs = []
    solver = data["solver"].unique()
    for i in range(min(len(s.split(",")) for s in solver)):
        if len({s.split(",")[i] for s in solver}) > 1:
            diffs.append(i)
    for i, s in enumerate(solver):
        print(
            f"Solver {i}:",
            ",".join(s.split(",")[i] for i in diffs),
            "with",
            len(data[data["solver"] == s]),
            "entries",
        )
