from ..instance_converter.dmsh import DmshGrid, GmshGrid
from ..solver_selection.abstract_solver import (
    PolygonInstanceSolver,
    PolygonInstanceSolverCallbacks,
)


class DmshAlgorithm(PolygonInstanceSolver):
    """Uses a mesh to compute a tour upon."""

    def __init__(
        self, full_coverage=False, point_based=False, hard_corners=False, scale=0.95
    ):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            DmshGrid(
                full_coverage=full_coverage,
                point_based=point_based,
                hard_corners=hard_corners,
                scale=scale,
            )
        )

    def identifier(self) -> str:
        return f"DmshAlgorithm({self.problem_converter})"


class GmshAlgorithm(PolygonInstanceSolver):
    """Uses a mesh to compute a tour upon."""

    def __init__(
        self,
        full_coverage=False,
        point_based=False,
        hard_corners=False,
        alg=9,
        quad=False,
        scale=1.0,
        callbacks=PolygonInstanceSolverCallbacks(),
    ):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            GmshGrid(
                full_coverage=full_coverage,
                point_based=point_based,
                hard_corners=hard_corners,
                alg=alg,
                quad=quad,
                scale=scale,
            ),
            callbacks=callbacks,
        )

    def identifier(self) -> str:
        return f"GmshAlgorithm({self.problem_converter})"


class MeshAlgorithm(PolygonInstanceSolver):
    """Uses a mesh to compute a tour upon."""

    def __init__(
        self,
        full_coverage=False,
        scale=0.95,
        integralization=50,
        cc_opt_steps=25,
        t_opt_steps=25,
        opt_size=50,
        callbacks=PolygonInstanceSolverCallbacks(),
    ):
        """
        full_coverage: Will enforce every point in the created grid to be covered. The
                        value of areas is ignored.
        point_based: If true, it will use a finer grid in which visiting every point will
                    result in a full coverage. Otherwise, it will use a rougher grid
                    where only parallel trajectories will result in a full coverage but
                    there will be some parts left at turns. By increasing the turn costs,
                    one can directly fund the additional costs for covering the missed
                    areas.
        """
        super().__init__(
            DmshGrid(
                full_coverage=full_coverage,
                point_based=False,
                hard_corners=True,
                scale=scale,
                dmsh_fallback=True,
            ),
            integralization=integralization,
            cc_opt_steps=cc_opt_steps,
            t_opt_steps=t_opt_steps,
            callbacks=callbacks,
            opt_size=opt_size,
        )

    def identifier(self) -> str:
        return f"MeshAlgorithm({self.problem_converter.scale}, full_coverage={self.problem_converter.full_coverage}, {self.grid_solver})"
