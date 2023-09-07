import pygame
from os.path import isfile, join
from os import listdir
from constants import *

from animation.init import Lift_Floor, Shuttle_Floor, Parking_Floor
from pygame.math import Vector2

FRAME_RATE = FPS * FACTOR


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def rotate(sprites, angle):
    return [pygame.transform.rotate(sprite, angle) for sprite in sprites]


def load_sprite_sheets(dir1, direction=False):
    path = join("assets", dir1)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprite_width, sprite_height = (
            sprite_sheet.get_width(),
            sprite_sheet.get_height(),
        )

        sprites = []
        surface = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA, 32)
        # surface.fill((255, 255, 255))
        rect = pygame.Rect(0, 0, sprite_width, sprite_height)
        surface.blit(sprite_sheet, (0, 0), rect)
        sprites.append(pygame.transform.scale(surface, (48, 48)))

        if direction:
            all_sprites[image.replace(".png", "") + "_up"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = rotate(sprites, 90)
            all_sprites[image.replace(".png", "") + "_down"] = rotate(sprites, 180)
            all_sprites[image.replace(".png", "") + "_right"] = rotate(sprites, 270)

        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def findCoord(level_layout, destObj):
    for sprite in level_layout.sprites():
        if (
            isinstance(sprite, Lift_Floor)
            and hasattr(destObj, "lift_num")
            and sprite.id == destObj.lift_num
        ):
            return sprite.rect.topleft
        elif (
            isinstance(sprite, Shuttle_Floor)
            and hasattr(destObj, "shuttle_num")
            and sprite.id == destObj.shuttle_num
        ):
            return sprite.rect.topleft
        elif isinstance(sprite, Parking_Floor) and sprite.id == destObj:
            # print(sprite)
            return sprite.rect.topleft


def findShuttle(level_layout, shuttle):
    for sprite in level_layout.sprites():
        if isinstance(sprite, Shuttle_Floor) and sprite.id == shuttle.shuttle_num:
            return sprite


def moveToGroundLift(vehicle, dest_coord, time_duration):
    dest_x, dest_y = dest_coord
    destination = Vector2(dest_x + vehicle.rect.width / 2, dest_y)
    vehicle.pos = Vector2(destination[0], destination[1] + 40)  # Spawn and put below
    velo = Vector2(0, (dest_y - vehicle.pos[1]) / (time_duration * FRAME_RATE))
    moveVehicle(vehicle, velo, destination)


def moveOutOfLift(vehicle, dest_coord, time_duration):
    dest_x, dest_y = (dest_coord[0], dest_coord[1] + 40)  # move out of lift
    destination = Vector2(dest_x + vehicle.rect.width / 2, dest_y)
    velo = Vector2(0, (dest_y - vehicle.pos[1]) / (time_duration * FRAME_RATE))
    moveVehicle(vehicle, velo, destination)
    vehicle.fade = True


def moveShuttle(shuttle_sprite, time_duration, coord, lift=False):
    dest_x, dest_y = coord

    if lift:
        dest_x += GRID_WIDTH

    sprite_x, sprite_y = shuttle_sprite.rect.x, shuttle_sprite.rect.y
    shuttle_sprite.destination = (dest_x, sprite_y)
    # print("shuttle: ", sprite.pos, sprite.destination)
    x = (dest_x - sprite_x) / (time_duration * FRAME_RATE)
    shuttle_sprite.velo = Vector2(x, 0)


def moveVehicle(vehicle, velo, dest, direction="up"):
    dest_x, dest_y = dest
    vehicle.destination = Vector2(dest_x, dest_y)
    vehicle.direction = direction
    vehicle.velo = Vector2(velo)


def moveLiftToPallet(vehicle, time_duration, coord):
    dest_x, dest_y = coord
    y = (dest_y - vehicle.pos[1]) / (time_duration * FRAME_RATE)
    moveVehicle(vehicle, (0, y), (vehicle.pos[0], dest_y))


def moveOriginToLot(vehicle, shuttle_sprite, time_duration, coord):
    moveShuttle(shuttle_sprite, time_duration, coord)
    velo_x = shuttle_sprite.velo[0]  # To maintain same speed as shuttle
    x_offset = (vehicle.rect.width - GRID_WIDTH) / 2
    moveVehicle(vehicle, (velo_x, 0), (coord[0] - x_offset, vehicle.pos[1]))


def rotateVehicle(vehicle, time_duration, coord):
    if time_duration == 0:
        return
    rotation_speed = 180 / (time_duration * FRAME_RATE)
    vehicle.rotation_speed = rotation_speed
    vehicle.final_ori = 180


def movePalletToLot(vehicle, time_duration, coord):
    dest_x, dest_y = coord
    y = (dest_y - vehicle.pos[1]) / (time_duration * FRAME_RATE)
    moveVehicle(vehicle, (0, y), (vehicle.pos[0], dest_y))
