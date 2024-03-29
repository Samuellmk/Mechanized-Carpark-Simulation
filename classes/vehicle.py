import pygame
from pygame.math import Vector2

from animation.utils import load_sprite_sheets
from constants import *

DIRECTION_MAP = {"up": 0, "right": 90, "down": 180, "left": 270}


def get_key_by_value(dict, value):
    for key, val in dict.items():
        if val == value:
            return key


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y, env, id, car_png, popup):
        super().__init__()
        self.car_png_name = car_png
        self.velo = Vector2(0, 0)
        self.SPRITES = load_sprite_sheets("Cars", True)
        self.direction = "up"
        self.pos = Vector2(x, y)
        self.sprite = self.SPRITES[self.car_png_name + "_" + self.direction][0]
        self.rect = self.sprite.get_rect(topleft=(x, y))
        self.destination = Vector2(0, 0)
        self.orientation = 0
        self.final_ori = 0
        self.rotation_speed = 0
        self.alpha = 255
        self.fade = False

        self.env = env
        self.id = id

        self.parking_lot = [None, None]  # (level, lot)

        self.popup = popup

    def update_sprite(self):
        sprite_sheet_name = self.car_png_name + "_" + self.direction
        self.sprite = self.SPRITES[sprite_sheet_name][0]
        # self.update()

    # def update(self):
    #     self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))

    def __call__(self, win):
        self.update_sprite()
        win.blit(self.sprite, (self.rect.x, self.rect.y))
        self.move()
        self.rotate()
        self.fading()

    def move(self):
        # logger.info(f"{self.id}: Check => {self.pos}  {self.rect.topleft}  {self.destination}")
        distance = self.destination - self.pos
        if distance.length() < TOLERANCE and self.velo != 0:
            self.velo = Vector2(0, 0)
            self.pos = Vector2(self.destination)
            self.rect.topleft = self.destination
            return

        self.pos += self.velo
        self.rect.topleft = (int(self.pos[0]), int(self.pos[1]))

    def fading(self):
        if self.fade:
            self.alpha = max(0, self.alpha - 2.5)  # alpha should never be < 0.
            self.sprite.fill(
                (255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT
            )
            if self.alpha <= 0:  # Kill the sprite when the alpha is <= 0.
                self.kill()

    def rotate(self):
        if (
            abs(self.final_ori - self.orientation) <= TOLERANCE
            and self.rotation_speed != 0
        ):
            self.rotation_speed = 0
            self.orientation = self.final_ori
            self.direction = get_key_by_value(
                DIRECTION_MAP, self.final_ori
            )  # Make sure is facing correctly

        self.orientation %= 360

        for direction, angle in DIRECTION_MAP.items():
            if abs(self.orientation - angle) < 90:
                self.direction = direction
                break

        self.orientation += self.rotation_speed
