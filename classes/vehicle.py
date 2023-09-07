import sys
import pygame
from pygame.math import Vector2
import simpy

from animation.utils import load_sprite_sheets
from constants import *

DIRECTION_MAP = {"up": 0, "right": 90, "down": 180, "left": 270}


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y, env, id):
        super().__init__()
        self.velo = Vector2(0, 0)
        self.SPRITES = load_sprite_sheets("Cars", True)
        self.direction = "up"
        self.pos = Vector2(x, y)
        self.sprite = self.SPRITES["Car_1_" + self.direction][0]
        self.rect = self.sprite.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.sprite)
        self.destination = Vector2(0, 0)
        self.orientation = 0
        self.final_ori = 0
        self.rotation_speed = 0
        self.alpha = 255
        self.fade = False

        self.env = env
        self.id = id

        self.parking_lot = [None, None]  # (level, lot)

    def update_sprite(self):
        sprite_sheet_name = "Car_1" + "_" + self.direction
        self.sprite = self.SPRITES[sprite_sheet_name][0]
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def __call__(self, win):
        self.update_sprite()
        win.blit(self.sprite, (self.rect.x, self.rect.y))
        self.move()
        self.rotate()
        self.fading()

    def move(self):
        # print("vehicle: ", self.pos, self.destination)
        distance = self.destination - self.pos
        if distance.length() < TOLERANCE:
            self.velo = Vector2(0, 0)
            self.pos = Vector2(self.destination)
            self.rect.topleft = self.destination
            return

        self.pos += self.velo
        self.rect.topleft = (int(self.pos[0]), int(self.pos[1]))

    def fading(self):
        if self.fade:
            print(self.alpha)
            self.alpha = max(0, self.alpha - 5)  # alpha should never be < 0.
            self.sprite.fill(
                (255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT
            )
            if self.alpha <= 0:  # Kill the sprite when the alpha is <= 0.
                self.kill()

    def rotate(self):
        if abs(self.final_ori - self.orientation) <= TOLERANCE:
            self.rotation_speed = 0
            self.orientation = self.final_ori

        self.orientation %= 360

        for direction, angle in DIRECTION_MAP.items():
            if abs(self.orientation - angle) < TOLERANCE:
                self.direction = direction
                break

        self.orientation += self.rotation_speed

    def run(self, carpark):
        parking_lot_request = carpark.total_parking_lot_resources.request()
        yield parking_lot_request
        vehicle = carpark.parking_queue.pop(0)

        yield self.env.process(carpark.park(vehicle))
        self.env.process(carpark.exit(vehicle, parking_lot_request))
