import pygame
import os
from os import listdir
from os.path import isfile, join
from classes.vehicle import Vehicle

from constants import *
from animation.utils import get_background
from animation.init import FloorLayout

import simpy
from simulation.init import sim_init
from simulation.utils import vehicle_arrival, set_stat_time
import numpy as np

import sys

from core import PyGameEnvironment, FrameRenderer
from vehicle import Vehicle
from animation.stats import StatsBox

np.random.seed(seed=RANDOM_SEEDS)

pygame.init()
pygame.display.set_caption("Mechanised Carpark Simulation")
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Background for the animation
background, bg_img = get_background("Blue.png")

renderer = FrameRenderer(window, background, bg_img)
env = PyGameEnvironment(renderer, factor=FACTOR, fps=FPS, strict=False)

# Setup carpark layout
floor_no = NUM_OF_LEVELS
carpark_layout = {}
for i in range(0, NUM_OF_LEVELS):
    floor_group = FloorLayout(level_number=floor_no, y_offset=i * 150 + STATS_HEIGHT)
    floor_group.create_floors_group()
    renderer.add(floor_group.floors_group)
    carpark_layout[floor_no] = floor_group.floors_group
    floor_no -= 1

# Stat Board
stats_box = StatsBox()
renderer.add(stats_box)

# init carpark class
carpark = sim_init(env, carpark_layout, stats_box)

# One vehicle
# vehicle = Vehicle(WIDTH // 2, 700, env, id=1)
# renderer.add(vehicle)

# carpark.parking_queue.append(vehicle)
# env.process(vehicle.run(carpark=carpark))


# Car Arrival
env.process(set_stat_time(env, stats_box))
env.process(vehicle_arrival(env, renderer, carpark, num_cars=MAX_CAR))

env.run()