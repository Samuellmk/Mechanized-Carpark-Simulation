import pygame
from constants import *


class Status_Tracker:
    def __init__(self, lifts_store, shuttles_stores):
        self.font = pygame.font.Font(pygame.font.match_font("arial"), 12)
        self.default_lifts = self.get_lifts(lifts_store)
        self.s_lifts = None
        self.s_shuttles = None
        self.parking_lots = None

    def get_lifts(self, lifts_store):
        lifts_num = []
        for lift in lifts_store.items:
            lifts_num.append(lift.num)

        return lifts_num

    def get_shuttles(self, shuttles_stores):
        shuttles_num = {}
        for idx, store in enumerate(shuttles_stores):
            shuttles_num[idx] = []
            for shuttle in store.items:
                shuttles_num[idx].append(shuttle.num)

        return shuttles_num

    def lifts_availability(self, win):
        s_lifts = self.get_lifts(self.s_lifts)
        y = 5
        for lift in self.default_lifts:
            word = f"Lift {lift}:"
            if lift in s_lifts:
                word += "Available"
                color = (85, 107, 47)
            else:
                word += "Unavailable"
                color = (255, 46, 46)
            text = self.font.render(word, True, color)
            text_rect = text.get_rect()
            text_rect.x = 5
            text_rect.y = y
            win.blit(text, text_rect)
            y += self.font.get_height()

        return y

    def shuttles_availability(self, win, start):
        s_shuttles = self.get_shuttles(self.s_shuttles)

        y = start

        for k, v in s_shuttles.items():
            word = f"Level {k+1}:"
            if len(v) > 0:
                word += ", ".join(map(str, v))
                color = (85, 107, 47)
            else:
                word += "None"
                color = (255, 46, 46)
            text = self.font.render(word, True, color)
            text_rect = text.get_rect()
            text_rect.x = 5
            text_rect.y = y
            win.blit(text, text_rect)
            y += self.font.get_height()

        return y

    def parking_lots_availability(self, win, start):
        y = start
        for lvl, parking_level in enumerate(self.parking_lots):
            word = f"Level {lvl}: {parking_level} lots"
            text = self.font.render(word, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.x = 5
            text_rect.y = y
            win.blit(text, text_rect)
            y += self.font.get_height()

    def __call__(self, win):
        bottom = self.lifts_availability(win)
        bottom = self.shuttles_availability(win, start=bottom + 10)
        self.parking_lots_availability(win, start=bottom + 10)
