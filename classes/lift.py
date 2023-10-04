"""
This is to get all the distances stored into each Lift classes,
as well as the availability of parking spaces for each lot
"""
from constants import *
import simpy


class Lift:
    def __init__(self, env, num, travel_times, default_level):
        self.env = env
        self.num = num
        self.travel_times = travel_times
        self.pos = default_level

    def time_taken_from_origin_to_dest(self, dest):
        time_taken = (abs(self.pos - dest)) * (HEIGHT_PER_LEVEL / LIFT_SPEED)

        return time_taken
