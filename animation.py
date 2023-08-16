import pygame
import os
from os import listdir
from os.path import isfile, join

pygame.init()
pygame.display.set_caption("Mechanised Carpark Simulation")

WIDTH, HEIGHT = 1200, 800
FPS = 60
CAR_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def rotate(sprites, angle):
    return [pygame.transform.rotate(sprite, angle) for sprite in sprites]


def load_sprite_sheets(dir1, width, height, direction=False):
    path = join("assets", dir1)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
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


def get_parking_floor(width, height):
    path = join("assets", "Floor", "floor_tiles.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    rect = pygame.Rect(64, 32, 32, 32)
    surface.blit(image, (0, 0), rect)
    scaled_surface = pygame.transform.scale2x(surface)

    bordered_surface = scaled_surface.copy()
    pygame.draw.rect(bordered_surface, (0, 0, 0), bordered_surface.get_rect(), 1)

    return bordered_surface


def get_lift_floor(width, height):
    path = join("assets", "Floor", "floor_tiles.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    rect = pygame.Rect(192, 0, 32, 32)

    repeat = round(width / 32)
    for i in range(repeat):
        surface.blit(image, (i * 32, 0), rect)

    scaled_surface = pygame.transform.scale2x(surface)

    bordered_surface = scaled_surface.copy()
    pygame.draw.rect(bordered_surface, (0, 0, 0), bordered_surface.get_rect(), 1)

    return bordered_surface


class Car(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    SPRITES = load_sprite_sheets("Cars", 256, 256, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def move_up(self, vel):
        self.y_vel = -vel
        if self.direction != "up":
            self.direction = "up"
            self.animation_count = 0

    def move_down(self, vel):
        self.y_vel = vel
        if self.direction != "down":
            self.direction = "down"
            self.animation_count = 0

    def loop(self, fps):
        self.move(self.x_vel, self.y_vel)

        self.update_sprite()

    def update_sprite(self):
        sprite_sheet_name = "Car_1" + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win):
        win.blit(self.sprite, (self.rect.x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))


class Parking_Floor(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        floor = get_parking_floor(width, height)
        self.image.blit(floor, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Lift_Floor(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        floor = get_lift_floor(width, height)
        self.image.blit(floor, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, car, objects):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
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


def main(window):
    clock = pygame.time.Clock()
    background, bg_img = get_background("Blue.png")

    parking_floor_size_width, parking_floor_size_height = 32, 48
    lift_floor_size_width, lift_floor_size_height = 96, 48

    car = Car(100, 100, 50, 50)

    floors = []
    for i in range(0, 26):
        floors.append(
            Parking_Floor(
                i * parking_floor_size_width,
                0,
                parking_floor_size_width,
                parking_floor_size_height,
            )
        )
        if i < 4:
            floors.append(
                Lift_Floor(
                    224 + (i * lift_floor_size_width),
                    96,
                    lift_floor_size_width,
                    lift_floor_size_height,
                )
            )

        if i < 7:
            floors.append(
                Parking_Floor(
                    i * parking_floor_size_width,
                    96,
                    parking_floor_size_width,
                    parking_floor_size_height,
                )
            )
        if i < 6:
            floors.append(
                Parking_Floor(
                    608 + (i * parking_floor_size_width),
                    96,
                    parking_floor_size_width,
                    parking_floor_size_height,
                )
            )

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

        car.loop(FPS)
        handle_move(car)
        draw(window, background, bg_img, car, floors)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
