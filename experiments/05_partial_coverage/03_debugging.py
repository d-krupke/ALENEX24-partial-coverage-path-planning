# %%

import matplotlib.pyplot as plt
from pcpptc import PolygonInstance
from pcpptc.plot import plot_polygon_instance, setup_plot

instance = "./instances2/11.instance.json"
instance = PolygonInstance.from_json(file_path=instance)

ax = setup_plot()
plot_polygon_instance(ax, instance)
plt.show()

# %%

from pcpptc import MeshAlgorithm

alg = MeshAlgorithm()
tour = alg(instance)

# %%

from pcpptc.plot import plot_solution

ax = setup_plot()
plot_polygon_instance(ax, instance)
plot_solution(ax, tour)
plt.show()
