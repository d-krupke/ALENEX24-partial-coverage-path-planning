import pygame
from pygame.locals import *
from pymunk import Vec2d

from .simulation import ParticleSimulation
from .transformer import BoundingBoxTransformer


class VisualizationLayer:
    """
    A layer for drawing in the visualization.
    """

    def draw(
        self,
        screen: pygame.Surface,
        transformer: BoundingBoxTransformer,
        simulation: ParticleSimulation,
    ):
        """
        screen: The screen used to draw on
        transformer: Transforming from physic engine to screen
        simulation: The particle simulation
        """
        raise NotImplementedError()


class Visualization:
    """
    The visualization. It is rather simple and allows no interaction but it is sufficient
    and should be compatible with most platforms. It also allows to add additional layer.
    """

    def __init__(self, simulation: ParticleSimulation):
        pygame.init()
        self.running = True
        self.simulation = simulation
        self.layer = []

        class RobotLayer(VisualizationLayer):
            def draw(
                self,
                screen: pygame.Surface,
                transformer: BoundingBoxTransformer,
                simulation: ParticleSimulation,
            ):
                for p in simulation.particles:
                    pygame.draw.circle(screen, "blue", transformer(p.position), 5)
                    pygame.draw.line(
                        screen,
                        "red",
                        transformer(p.position),
                        transformer(p.position + p.force),
                        3,
                    )
                for s in simulation.segments:
                    pygame.draw.line(
                        screen, "grey", transformer(s.a), transformer(s.b), 3
                    )

        self.add_layer(RobotLayer())

    def add_layer(self, layer: VisualizationLayer):
        self.layer.append(layer)

    def run(self, screen_size=(1000, 1000), dt=0.1):
        pygame.init()
        screen = pygame.display.set_mode(screen_size, HWSURFACE | DOUBLEBUF | RESIZABLE)
        margin = Vec2d(15.0, 15.0)
        print(self.simulation.get_bounding_box())
        transformer = BoundingBoxTransformer(
            source_bb=self.simulation.get_bounding_box(),
            target_bb=(margin, Vec2d(*screen_size) - 2 * margin),
        )

        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.display.quit()
                    self.running = False
                    pygame.quit()
                    return
                elif event.type == VIDEORESIZE:
                    transformer = BoundingBoxTransformer(
                        source_bb=self.simulation.get_bounding_box(),
                        target_bb=(margin, Vec2d(*event.size) - 2 * margin),
                    )
                    screen = pygame.display.set_mode(
                        event.size, HWSURFACE | DOUBLEBUF | RESIZABLE
                    )

            screen.fill("white")
            for layer in self.layer:
                layer.draw(screen, transformer, self.simulation)
            pygame.display.update()
            self.simulation.step(dt)
        pygame.quit()
