import pygame
from simpy.rt import RealtimeEnvironment
from classes.vehicle import Vehicle


class PyGameEnvironment(RealtimeEnvironment):
    """
    Customized version of ``simpy.rt.RealtimeEnvironment`` that attempts to
    maintain a steady framerate.

    :param renderer: what we use to draw the simulation
    :type renderer: :class:`~simpygame.core.FrameRenderer`
    :param fps: intended frames per second
    :param args: other arguments passed blindly to ``simpy.rt.RealtimeEnvironment``
    :param kwargs: other arguments passed blindly to ``simpy.rt.RealtimeEnvironment``
    """

    def __init__(self, renderer, fps=30, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_pygame_quit = self.event()
        self._renderer = renderer
        self._ticks_per_frame = 1.0 / (self.factor * fps)

    def _render(self):
        while True:
            if self._pygame_quit_requested():
                self._on_pygame_quit.succeed()

            self._renderer.render()

            yield self.timeout(self._ticks_per_frame)

    def _pygame_quit_requested(self):
        quit_events = (e for e in pygame.event.get() if e.type == pygame.QUIT)
        return any(quit_events)

    def run(self):
        """
        Runs the simulation until a ``pygame.QUIT`` event is received
        """
        self.process(self._render())
        super().run(until=self._on_pygame_quit)


class FrameRenderer(object):
    """
    Renders the state of the simulation to a ``pygame`` display.

    :param screen: a ``pygame`` display that gets passed to every draw function added via :meth:`add`
    """

    def __init__(self, screen, background, bg_image):
        self._screen = screen
        self._callbacks = []
        self._background = background
        self._bg_image = bg_image
        self.vehicle_group = pygame.sprite.Group()

    def check_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_rect = pygame.Rect(
            mouse_x, mouse_y, 1, 1
        )  # Create a small Rect at the mouse position

        for vehicle in self.vehicle_group:
            if vehicle.rect.colliderect(mouse_rect):
                # If the vehicle collides with the mouse cursor
                vehicle.popup.show((mouse_x, mouse_y))
            else:
                # If the vehicle doesn't collide with the mouse cursor
                vehicle.popup.hide()

    def render(self):
        """
        Fills the screen with *fill_color*, then calls all draw functions, then
        updates the screen with ``pygame.display.flip``.
        """

        for tile in self._background:
            self._screen.blit(self._bg_image, tile)

        for draw in self._callbacks:
            if isinstance(draw, pygame.sprite.Group):
                for sprite in draw.sprites():
                    sprite(win=self._screen)
            else:
                draw(win=self._screen)

        # Render all the vehicles before rendering all the popup
        for vehicle in self.vehicle_group:
            vehicle(win=self._screen)

        for vehicle in self.vehicle_group:
            vehicle.popup.render(self._screen)

        self.check_mouse()

        pygame.display.flip()

    def add(self, drawable):
        """
        add a draw function to be called on every frame
        """

        if isinstance(drawable, Vehicle):
            self.vehicle_group.add(drawable)
        else:
            self._callbacks.append(drawable)
