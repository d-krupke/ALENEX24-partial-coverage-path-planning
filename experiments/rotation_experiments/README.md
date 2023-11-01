# Rotation Experiments

These experiments analyse the importance of the correct rotation for the
coverage costs and the covered area. We analyse

- How square and hexagonal grids compare
- How point based and line based grid sizes compare. Point based has a (nearly)
  full coverage by only visiting the points. Line based is complete on parallel
  movements but misses parts in turns. By adding some extra costs, the missing
  parts at these turns could be covered, too.
- How much influence the ratio of turn costs has

The data is saved in pandas readable form in
[./data/results.json](./data/results.json). The corresponding code can be found
in [./run_new.py](./run_new.py)

- It runs 30x for random grids for square/hexagonal and point/line based.
- It runs with rotated grid
- It runs the experimental solver _which probably changed a lot and is not
  really comparable!_
