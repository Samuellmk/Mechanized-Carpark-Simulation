import pygame
import os
from os import listdir
from os.path import isfile, join
from classes.vehicle import Vehicle

from constants import *
from animation.utils import load_sprite_sheets
from classes.object import Object
from animation.init import layout_init, Wall_Borders, Shuttle_Floor

import simpy
from simulation.init import sim_init
from simulation.utils import vehicle_arrival
import numpy as np

pygame.init()
pygame.display.set_caption("Mechanised Carpark Simulation")
window = pygame.display.set_mode((WIDTH, HEIGHT))


def draw(window, background, bg_image, car, carpark):
    for tile in background:
        window.blit(bg_image, tile)

    for level in carpark:
        # for obj in level:
        #     if isinstance(obj, Shuttle_Floor):
        #         obj.move()

        for obj in level:
            if isinstance(obj, Wall_Borders):
                obj.draw(window)

        for obj in level:
            if not isinstance(obj, Wall_Borders):
                obj.draw(window)

    car.draw(window)

    pygame.display.update()


def handle_move(car):
    keys = pygame.key.get_pressed()

    car.x_vel = 0
    car.y_vel = 0
    if keys[pygame.K_LEFT]:
        car.move_left(CAR_VEL)
    if keys[pygame.K_RIGHT]:
        car.move_right(CAR_VEL)
    if keys[pygame.K_UP]:
        car.move_up(CAR_VEL)
    if keys[pygame.K_DOWN]:
        car.move_down(CAR_VEL)


def main():
    # Simpy setup
    env = simpy.rt.RealtimeEnvironment(factor=1, strict=False)
    np.random.seed(seed=RANDOM_SEEDS)
    carpark = sim_init(env)

    # Animation setup
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks() / 1000.0
    carpark_layout, background, bg_img = layout_init()

    car = Vehicle(
        100, HEIGHT / 2, 50, 50, load_sprite_sheets("Cars", 256, 256, True), env
    )

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        carpark.parking_queue.append(1)
        print("Car %s arrived at the entrance of the carpark at %.2f." % (1, env.now))
        car.request_lot(carpark)

        env.run(until=pygame.time.get_ticks() / 1000.0 - start_time)

        car.loop()
        handle_move(car)
        draw(window, background, bg_img, car, carpark_layout)

        clock.tick(FPS)
    pygame.quit()
    quit()


if __name__ == "__main__":
    main()
