from constants import *
import simpy


class Lobby:
    def __init__(self, env, num, travel_times):
        self.env = env
        self.num = num
        self.travel_times = travel_times
        self.pos = 0

    def time_taken_from_origin_to_dest(self, dest):
        time_taken = (abs(self.pos - dest)) * (HEIGHT_PER_LEVEL / LIFT_SPEED)

        return time_taken
