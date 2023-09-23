import pygame
import sys
from os import listdir
from os.path import isfile, join
from pygame.math import Vector2

from constants import *


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, id=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.id = id

    def __call__(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))

    def add_text(self, text, font_size):
        font = pygame.font.Font(pygame.font.match_font("arial"), font_size)
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.image.get_rect().center)
        self.image.blit(text_surface, text_rect.topleft)


def generate_floor_texture(
    width, height, base_image_path, source_rect, border_color=None
):
    # Load the base image
    image = pygame.image.load(base_image_path).convert_alpha()

    # Create a surface for the floor
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)

    # Calculate the number of times to repeat the base image horizontally
    repeat_x = width // source_rect.width

    for i in range(repeat_x):
        x_offset = i * source_rect.width
        surface.blit(image, (x_offset, 0), source_rect)

    # Scale the surface to fit the specified width and height
    scaled_surface = pygame.transform.scale2x(surface)

    # Create a bordered version of the surface
    bordered_surface = scaled_surface.copy()
    if border_color:
        pygame.draw.rect(bordered_surface, border_color, bordered_surface.get_rect(), 1)

    return bordered_surface


class Parking_Floor(Object):
    def __init__(self, x, y, width, height, id):
        super().__init__(x, y, width, height, id)
        floor = generate_floor_texture(
            width,
            height,
            join("assets", "Floor", "floor_tiles.png"),
            pygame.Rect(64, 32, 32, 32),
            (0, 0, 0),
        )
        self.image.blit(floor, (0, 0))
        self.add_text("P" + str(id), 18)


class Lift_Floor(Object):
    def __init__(self, x, y, width, height, id, level_no):
        super().__init__(x, y, width, height, id)
        self.id = id
        self.floor = generate_floor_texture(
            width,
            height,
            join("assets", "Floor", "floor_tiles.png"),
            pygame.Rect(192, 0, 32, 32),
            (0, 0, 0),
        )
        self.is_Occupied = False
        self.default_state(level_no)
        self.set_overlay()

    def default_state(self, id):
        if id == DEFAULT_LIFT_STATE:
            self.toggle_Occupancy()

    def set_overlay(self):
        self.image.blit(self.floor, (0, 0))
        self.add_text("Lift " + str(self.id), 18)
        if not self.is_Occupied:
            surface = pygame.Surface(
                (self.image.get_width(), self.image.get_height()), pygame.SRCALPHA
            )
            surface.fill((106, 106, 106, 178))  # 60%
            self.image.blit(surface, (0, 0))

    def toggle_Occupancy(self):
        self.is_Occupied = not self.is_Occupied
        self.set_overlay()


class Shuttle_Floor(Object):
    def __init__(self, x, y, width, height, id, bounds):
        super().__init__(x, y, width, height, id)
        floor = generate_floor_texture(
            width,
            height,
            join("assets", "Shuttle", "doortile.png"),
            pygame.Rect(0, 0, 32, 32),
            (0, 0, 0),
        )
        self.image.blit(floor, (0, 0))
        self.add_text("S" + str(id), 18)
        self.velo = Vector2(0, 0)
        self.pos = Vector2(x, y)
        self.destination = Vector2(0, 0)
        self.default_pos = Vector2(x, y)
        self.bounds = bounds

    def move(self):
        # logger.info("bounds: ", self.bounds)

        self.pos[0] = max(self.bounds[0], min(self.pos[0], self.bounds[1]))
        distance = self.destination - self.pos
        if distance.length() < TOLERANCE and self.velo != 0:
            self.velo = Vector2(0, 0)
            self.pos = Vector2(self.destination)
            self.rect.topleft = self.destination
            return

        self.pos += self.velo
        self.rect.topleft = (int(self.pos[0]), int(self.pos[1]))

    def __call__(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))
        self.move()


class Wall_Borders(Object):
    def __init__(self, floors_group, id):
        super().__init__(0, 0, 0, 0, id)
        self.floors_group = floors_group
        self.update_rect()

    def update_rect(self):
        # Calculate the bounding rectangle that encloses all floor objects
        if len(self.floors_group) > 0:
            left = min(floor.rect.left for floor in self.floors_group) - 2
            top = min(floor.rect.top for floor in self.floors_group) - 2
            right = max(floor.rect.right for floor in self.floors_group) + 2
            bottom = max(floor.rect.bottom for floor in self.floors_group) + 2

            self.rect = pygame.Rect(left, top, right - left, bottom - top)
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)

    def __call__(self, win):
        pygame.draw.rect(win, (106, 106, 106), self.rect)
        pygame.draw.rect(win, (0, 0, 0), self.rect, 2)

        if self.id:
            font = pygame.font.Font(None, 24)
            text_surface = font.render(self.id, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=self.rect.center)
            win.blit(text_surface, text_rect)


class FloorLayout(pygame.sprite.Group):
    def __init__(self, y_offset, level_number):
        self.horizontal_offset = (WIDTH - TOTAL_WIDTH) // 2
        self.y_offset = y_offset
        self.GRID_WIDTH = GRID_WIDTH
        self.GRID_HEIGHT = GRID_HEIGHT
        self.level_number = level_number
        self.TOTAL_WIDTH = TOTAL_WIDTH
        self.floors_group = pygame.sprite.Group()

    def create_floors_group(self):
        floors_group_list = []
        self.create_parking_floors(floors_group_list)
        self.create_lift_floors(floors_group_list)
        self.create_south_parking_floors(floors_group_list)
        self.create_wall_borders(floors_group_list)
        floors_group_list.reverse()
        for sprite in floors_group_list:
            self.floors_group.add(sprite)

    def create_wall_borders(self, floors_group):
        wall_borders = Wall_Borders(floors_group, "Level " + str(self.level_number))
        floors_group.append(wall_borders)

    def create_parking_floors(self, floors_group):
        for i in range(0, 26):
            floors_group.append(
                Parking_Floor(
                    self.horizontal_offset + i * self.GRID_WIDTH,
                    self.y_offset,
                    self.GRID_WIDTH,
                    self.GRID_HEIGHT,
                    i + 1,
                )
            )
        for i, floor_number in enumerate(range(27, 34)):
            floors_group.append(
                Parking_Floor(
                    self.horizontal_offset + i * self.GRID_WIDTH,
                    self.y_offset + 96,
                    self.GRID_WIDTH,
                    self.GRID_HEIGHT,
                    floor_number,
                )
            )

    def create_lift_floors(self, floors_group):
        lift_offset = self.horizontal_offset + 224
        for i, lift_no in enumerate(range(1, 5)):
            floors_group.append(
                Lift_Floor(
                    lift_offset + i * (3 * self.GRID_WIDTH),
                    self.y_offset + 96,
                    3 * self.GRID_WIDTH,
                    self.GRID_HEIGHT,
                    lift_no,
                    self.level_number - 1,
                )
            )

    def create_south_parking_floors(self, floors_group):
        parking_offset_south = self.horizontal_offset + 608
        for i, parking_no in enumerate(range(34, 40)):
            floors_group.append(
                Parking_Floor(
                    parking_offset_south + i * self.GRID_WIDTH,
                    self.y_offset + 96,
                    self.GRID_WIDTH,
                    self.GRID_HEIGHT,
                    parking_no,
                )
            )
        position_13 = self.horizontal_offset + GRID_WIDTH * 12
        floors_group.append(
            Shuttle_Floor(
                position_13,
                self.y_offset + 48,
                self.GRID_WIDTH,
                self.GRID_HEIGHT,
                id=1,
                bounds=(
                    self.horizontal_offset,
                    self.horizontal_offset + GRID_WIDTH * 26,
                ),
            )
        )
