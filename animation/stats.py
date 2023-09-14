import pygame
from constants import *
from os.path import join
import numpy as np


class StatsBox:
    def __init__(self):
        self.waiting_stats = {
            "parking": [0] * MAX_CAR,
            "retrieval": [0] * MAX_CAR,
        }
        self.stats = {
            "Total Car Served": 0,
            "Cars Parked": 0,
            "Cars Exited": 0,
            "Cars Waiting": 0,
            "Tick": 0.0,
            "Actual Time": 0.0,
            "Avg. Parking Waiting Time": 0,
            "Avg. Retrieval Waiting Time": 0,
        }
        self.background = self.get_background()

    def get_background(self):
        # Load the large image
        large_image = pygame.image.load(
            join("assets", "Background", "TileableWall.png")
        )

        tile = pygame.transform.scale(
            large_image,
            (STATS_HEIGHT, STATS_HEIGHT),
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
        for x in range(num_tiles_x):
            for y in range(num_tiles_y):
                background_surface.blit(tile, (x * STATS_HEIGHT, y * STATS_HEIGHT))

        return background_surface

    def calculate_waiting_time(self):
        self.stats["Avg. Parking Waiting Time"] = round(
            np.mean(self.waiting_stats["parking"]), 3
        )
        self.stats["Avg. Retrieval Waiting Time"] = round(
            np.mean(self.waiting_stats["retrieval"]), 3
        )

    def calculate_actual_time(self):
        # Calculate hours
        hours = int(self.stats["Tick"] / 60) % 24

        # Calculate remaining minutes
        remaining_minutes = int(self.stats["Tick"] % 60)

        # Calculate seconds
        seconds = int((self.stats["Tick"] % 1) * 60)

        # Format the time as H:mm:ss
        self.stats["Actual Time"] = f"{hours:02}:{remaining_minutes:02}:{seconds:02}"

    def change_color(self, key, value):
        default_color = (255, 255, 255)
        if key == "Avg. Parking Waiting Time" or key == "Avg. Retrieval Waiting Time":
            if value >= 5.0:
                default_color = (255, 46, 46)
            elif value >= 2.0:
                default_color = (255, 191, 0)

        elif key == "Cars Waiting":
            if value >= 10:
                default_color = (255, 46, 46)
            elif value >= 5:
                default_color = (255, 191, 0)

        return default_color

    def __call__(self, win):
        self.stats["Total Car Served"] = (
            self.stats["Cars Parked"] + self.stats["Cars Exited"]
        )

        # Calculate the actual time
        self.calculate_actual_time()

        font = pygame.font.Font(pygame.font.match_font("arial"), 18)
        board_y = win.get_height() - STATS_HEIGHT
        win.blit(self.background, (0, board_y))

        x, y = 10, board_y + 6
        for label, value in self.stats.items():
            color = self.change_color(label, value)
            if label == "Avg. Parking Waiting Time":
                x = 10
                y += STATS_HEIGHT / 2
            text = f"{label}: {value}"
            text_surface = font.render(text, True, color)
            win.blit(text_surface, (x, y))
            x += text_surface.get_width() + 20

        # Calculate the waiting time
        self.calculate_waiting_time()
