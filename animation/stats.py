import pygame
from constants import *
from os.path import join


class StatsBox:
    def __init__(self):
        self.stats = {
            "Total Car Served": 0,
            "Cars Parked": 0,
            "Cars Exited": 0,
            "Tick": 0.0,
            "Avg. Parking Waiting Time": 0,  # TODO: make a function for these two
            "Avg. Retrieval Waiting Time": 0,
        }
        self.background = self.get_background()

    def get_background(self):
        # Load the large image
        large_image = pygame.image.load(
            join("assets", "Background", "TileableWall.png")
        )

        # Set the desired size for your background (e.g., the size of your StatsBox)
        background_width = WIDTH
        background_height = STATS_HEIGHT

        # Create a new surface for the background
        background_surface = pygame.Surface((background_width, background_height))

        # Calculate the number of tiles needed in both X and Y directions
        num_tiles_x = background_width // STATS_HEIGHT + 1
        num_tiles_y = background_height // STATS_HEIGHT

        # Blit the large image onto the background surface in a grid pattern
        background_tiles = []
        for x in range(num_tiles_x):
            for y in range(num_tiles_y):
                tile = pygame.transform.scale(
                    large_image,
                    (STATS_HEIGHT, STATS_HEIGHT),
                )
                background_surface.blit(tile, (x * 26, y * 26))
        print(background_surface)
        return background_surface

    def __call__(self, win):
        self.stats["Total Car Served"] = (
            self.stats["Cars Parked"] + self.stats["Cars Exited"]
        )

        board_height = STATS_HEIGHT
        board_rect = pygame.draw.rect(
            win, (200, 200, 200), (0, 0, win.get_width(), board_height)
        )

        x, y = 10, 3
        font = pygame.font.Font(pygame.font.match_font("arial"), 16)
        win.blit(self.background, (0, 0))

        for label, value in self.stats.items():
            text = f"{label}: {value}"
            text_surface = font.render(text, True, (255, 255, 255))
            win.blit(text_surface, (x, y))
            x += text_surface.get_width() + 20
