"""
This is a particle simulation to simulate particles with some forces in a polygonal
environment.
You implement a force by inheriting from `Force`.
Then you add it to some particles which you add to the simulation.
Then you add a polygonal environment to keep the particles within.
Simulate it using the visualization or calling the loop-method.

It is meant to be simple.

Because you have to have the proper number ranges (it seems like distances below 1 become
very inaccurate), there are some transformer. However, maybe the forces/impulses in my
experiments simply have been to high and you actually do not need that.
"""

