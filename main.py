import pygame

from constants import *
from animation.utils import get_background
from animation.init import FloorLayout

from simulation.init import sim_init
from simulation.utils import vehicle_arrival, collect_floor
import numpy as np

from core import PyGameEnvironment, FrameRenderer
from animation.stats import StatsBox

import multiprocessing


def simulation(instance_type):
    np.random.seed(seed=RANDOM_SEEDS)

    pygame.init()
    pygame.display.set_caption(f"Mechanised Carpark Simulation - {instance_type}")
    window = pygame.display.set_mode((WIDTH, HEIGHT))

    # Background for the animation
    background, bg_img = get_background("Blue.png")

    renderer = FrameRenderer(window, background, bg_img)
    env = PyGameEnvironment(renderer, factor=FACTOR, fps=FPS, strict=False)

    # Setup carpark layout
    floor_no = NUM_OF_LEVELS
    carpark_layout = {}
    for i in range(0, NUM_OF_LEVELS):
        floor_group = FloorLayout(level_number=floor_no, y_offset=i * 150 + 12)
        floor_group.create_floors_group()
        renderer.add(floor_group.floors_group)
        carpark_layout[floor_no] = floor_group.floors_group
        floor_no -= 1

    # Stat Board
    stats_box = StatsBox()
    renderer.add(stats_box)

    # init carpark class
    carpark = sim_init(env, carpark_layout, stats_box)
    carpark.policy = instance_type

    # Car Arrival
    env.process(collect_floor(env, carpark))
    env.process(stats_box.set_stat_time(env, stats_box))
    env.process(vehicle_arrival(env, renderer, carpark))

    env.run()
    stats_box.show_stats(carpark, instance_type)


if __name__ == "__main__":
    # # Define the number of parallel simulations
    # simulations_type = ["Nearest-First"]  # , "Randomised"]  # Adjust as needed

    # # Create a list to store process objects
    # processes = []

    # for type in simulations_type:
    #     process = multiprocessing.Process(target=simulation, args=(type,))
    #     processes.append(process)
    #     process.start()

    # # Wait for all processes to finish
    # for process in processes:
    #     process.join()
    simulation("Nearest-First")
