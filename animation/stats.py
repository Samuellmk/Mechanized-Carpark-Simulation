import pygame
from constants import *
from os.path import join
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.gridspec import GridSpec
import seaborn as sns


class StatsBox:
    def __init__(self, logger):
        # TODO: Utilization stats
        self.utilization_stats = {"floors": [[] for _ in range(NUM_OF_LEVELS)]}
        # Track the time after driver drove in to parking spot,
        # Track the time from parking spot to before driver drive vehicle out
        self.service_stats = {"parking": {}, "retrieval": {}}
        self.waiting_stats = {"parking": {}, "retrieval": {}}

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
        self.logger = logger

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
        if self.waiting_stats["parking"]:
            parking = list(self.waiting_stats["parking"].values())
            retrieval_list = list(self.waiting_stats["retrieval"].values())
            self.stats["Avg. Parking Waiting Time"] = round(np.mean(parking), 3)
            self.stats["Avg. Retrieval Waiting Time"] = round(
                np.mean(retrieval_list), 3
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
        red = (255, 46, 46)
        amber = (255, 191, 0)
        if key == "Avg. Parking Waiting Time" or key == "Avg. Retrieval Waiting Time":
            if value >= 5.0:
                default_color = red
            elif value >= 2.0:
                default_color = amber

        elif key == "Cars Waiting":
            if value >= 10:
                default_color = red
            elif value >= 5:
                default_color = amber

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

    def set_stat_time(self, env, stats_box):
        while True:
            stats_box.stats["Tick"] = round(env.now, 2)
            yield env.timeout(0.1)

    def show_stats(self, carpark, instance_type):
        self.logger.info("=============STATISTICS=============")
        parking_dict = self.waiting_stats["parking"]
        retrieval_dict = self.waiting_stats["retrieval"]
        service_parking_dict = self.service_stats["parking"]
        service_retrieval_dict = self.service_stats["retrieval"]
        floors_occupancy = self.utilization_stats["floors"]

        sns.set(style="whitegrid")
        fig = plt.figure(figsize=(16, 8))
        fig.canvas.manager.set_window_title(f"{instance_type} Policy")
        gs = GridSpec(3, 2)  # 3 rows, 2 columns

        ax1 = fig.add_subplot(gs[0, 0])  # First row, first column
        ax2 = fig.add_subplot(gs[0, 1])  # First row, second column
        ax3 = fig.add_subplot(gs[1, 0])  # Second row, first column
        ax4 = fig.add_subplot(gs[1, 1])  # Second row, second column
        ax5 = fig.add_subplot(gs[2, :])  # Second row, span all column

        self.plot_waiting_service_time(parking_dict, "waiting", "Parking", ax1)
        self.plot_waiting_service_time(retrieval_dict, "waiting", "Retrieval", ax2)
        self.plot_waiting_service_time(service_parking_dict, "service", "Parking", ax3)
        self.plot_waiting_service_time(
            service_retrieval_dict, "service", "Retrieval", ax4
        )
        self.plot_floors_trend(floors_occupancy, "Level", ax5)

        plt.tight_layout()
        plt.show()

    def plot_waiting_service_time(self, wait_dict, catergory_title, title, ax):
        # Extract data from the waiting_times dictionary
        labels = list(wait_dict.keys())
        times = list(wait_dict.values())

        mean_time = np.mean(times)
        self.logger.info(
            f"Mean of {catergory_title} time for a vehicle {title.lower()}: {mean_time:.2f}"
        )

        # Plot the data as a bar chart
        sns.barplot(
            x=labels,
            y=times,
            lw=0.0,
            ax=ax,
        )
        ax.set_xlabel("Car ID")
        ax.set_ylabel(f"{catergory_title.capitalize()} Time for {title} (mins)")
        ax.set_title(f"{catergory_title.capitalize()} Time for {title} of Vehicles")
        ax.set_xticks(np.arange(0, len(labels) + 1, 30))
        ax.set_xticklabels(ax.get_xticks(), rotation=45)

    def plot_floors_trend(self, floors, title, ax):
        times = np.arange(0, len(floors[0]) * 5, 5)

        for idx, floor in enumerate(floors):
            label = f"Floor {idx+1}"
            sns.lineplot(x=times, y=floor, ax=ax, label=label)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.set_xlabel("Time (Interval of 5 mins)")
        ax.set_ylabel(f"Parking Occupancy/Level")
        ax.set_title(f"{title} {idx+1}")
        ax.set_xticklabels(ax.get_xticks(), rotation=45)
        ax.legend()
