# ALENEX 2024: Near-Optimal Coverage Path Planning with Turn Costs (Code and Data)

*Dominik Krupke, 2023, TU Braunschweig, Germany*

**Abstract:**

>  Coverage path planning is a fundamental challenge in robotics, with diverse applications in aerial surveillance, manufacturing, cleaning, inspection, agriculture, and more.
>  The main objective is to devise a trajectory for an agent that efficiently covers a given area,
>  while minimizing time or energy consumption.
>  Existing practical approaches often lack a solid theoretical foundation, relying on purely heuristic methods,
>  or overly abstracting the problem to a simple Traveling Salesman Problem in Grid Graphs.
>  Moreover, the considered cost functions only rarely consider turn cost, prize-collecting variants for uneven cover demand, or arbitrary geometric regions.
>
>  In this paper, we describe an array of systematic methods for handling arbitrary meshes derived from intricate, polygonal environments.
>  This adaptation paves the way to compute efficient coverage paths with a robust theoretical foundation for real-world robotic applications.
>  Through comprehensive evaluations, we demonstrate that the algorithm also exhibits low optimality gaps, while efficiently handling complex environments. 
>  Furthermore, we showcase its versatility in handling partial coverage and accommodating heterogeneous passage costs, offering the flexibility to trade off coverage quality and time efficiency.

**Full Version:** [https://arxiv.org/abs/2310.20340](https://arxiv.org/abs/2310.20340)

Given a polygon containing the feasible positions of a circular robot and a set
of weighted polygons for value of the area and a cost multiplier. We compute a
tour that optimizes covered value minus the cost based on distance and turn
angles (locally multiplied by the expensive areas).

**Approach:**

1. Generate a grid that fits the polygonal environment. Determine coverage value
   for grid points and the local touring costs.
2. Compute a (penalty) cycle cover on the grid
   1. Solve fractional cycle cover on it. Possibly extended with some additional
      constraints to make it more integral and more toury.
   2. Select atomic strips
   3. Match the atomic strips via a minimum weight perfect matching, creating a
      cycle cover
3. Connect to a tour.

<img src="./.assets/example.png" alt="example" width="400">

You can find a more detailed problem description in the
[polgyon_instance module](src/pcpptc/polygon_instance/__init__.py).

See [this example](./examples/example_algorithm_steps.ipynb) to get an
impression of the individual steps.

## Installation

> :warning: **The code in this repository does not allow to reproduce the smooth
> meshes unless you have by chance older versions of *dmsh* and *optimesh* installed.
> The open source versions of these package have unfortunately been removed from GitHub
> and PyPI and been replaced by commercial packages. More below.**

We are using the Gurobi solver. You can get a free academic license on their
website. If you do not have a license installed, you can probably not run any
non-trivial instances. During the installation, the Python-package will
automatically be installed. If you need to set up a license, we recommend
installing Gurobi via conda, as this will also install the necessary tools for
license management.

You can build and install this package via cloning the repository and running

```bash
pip install .
```

This should automatically install all further dependencies. The code still has
some legacy parts for which no package will be installed, but you should not
need them.

### More on the problem with dmsh and optimesh

The project used *dmsh* and *optimesh* as fundamental elements to create
good meshes. While *dmsh* can be replaced easily with only little loss,
*optimesh* is very important for smoothing the grids. Both modules have
been open source projects (MIT/GPL3) while we were developing the tools,
but now have changed to a commercial license that requires a subscription
of 50Euro per year for two workstations. I can understand that a developer
wants to monetize a great product, but it is very unfortunate that they
completely removed the old versions from GitHub and from PyPI. Thus, the
old virtual environments can no longer be installed.

There are citable, archived versions still under open source license of both modules on zenodo (like arxiv for code by CERN):

* [https://zenodo.org/record/5019221](https://zenodo.org/record/5019221)
* [https://zenodo.org/record/4728056](https://zenodo.org/record/4728056)

However, the dependency meshplex is not. Versions of it are available as Debian-archives,
but Unfortunately not in the right version.
We still have the right version on our workstations, but only the raw code with a license file,
but no attribution etc.
We guess that we can make the old open source versions fit together somehow,
and add them to this package, just so it remains usable, but we first have to
check the conditions under which we are allowed to do so.

## Experiments

The full experiments have a size of around 1GB even when compressed, thus, they
may be missing in the repository.

- [./experiments/01_grid](./experiments/01_grid) provides a number of
  experiments regarding the grid.
- [./experiments/02_algorithm_explanation](./experiments/02_algorithm_explanation)
  provides visualizations and examples of the individual steps.
- [./experiments/03_grids_in_detail](./experiments/03_grids_in%20_detail)
  provides additional experiments for the grid.
- [./experiments/05_partial_coverage](./experiments/05_partial_coverage)
  provides experiments for partial coverage.
- [./experiments/06_optimizations](./experiments/06_optimizations) provides
  experiments regarding optimizations.
- [./experiments/rotation_experiments](./experiments/rotation_experiments)
  provides experiments regarding the optimal orientation of the grid.

Most of the corresponding jupyter notebooks that evaluate the experiments
contain a documentation and explanation.

## Notes

This project was developed from 2020-2022 as a (pretty large) side project, and
updated end of 2023 to make it ready for publication as some dependencies became
incompatible or were no longer available. It has a huge code base, as it took
many iterations to finally get satisfying results. A lot of the failed ideas
have been removed, but some are still (partially) contained. Equally, while some
parts of the code are reasonably clean (especially the difficult ones that
required evaluation), others are not.
