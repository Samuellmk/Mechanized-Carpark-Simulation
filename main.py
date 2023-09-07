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
from simulation.utils import vehicle_arrival
import numpy as np

import sys

from core import PyGameEnvironment, FrameRenderer
from vehicle import Vehicle

pygame.init()
pygame.display.set_caption("Mechanised Carpark Simulation")
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Background for the animation
background, bg_img = get_background("Blue.png")

renderer = FrameRenderer(window, background, bg_img)
env = PyGameEnvironment(renderer, factor=FACTOR, fps=FPS, strict=False)  # 4x speed

# Setup carpark layout and init carpark class
floor_no = 4
carpark_layout = {}
for i in range(0, 4):
    floor_group = FloorLayout(level_number=floor_no, y_offset=i * 150)
    floor_group.create_floors_group()
    renderer.add(floor_group.floors_group)
    carpark_layout[floor_no] = floor_group.floors_group
    floor_no = floor_no - 1
carpark = sim_init(env, carpark_layout)

# One vehicle
vehicle = Vehicle(WIDTH / 2, 600, env, id=0)
renderer.add(vehicle)

carpark.parking_queue.append(vehicle)
env.process(vehicle.run(carpark=carpark))

env.run()
