"""
This is to get all the distances stored into each Lift classes,
as well as the availability of parking spaces for each lot
"""
from constants import *
import simpy


class Lift:
    def __init__(self, env, lift_num, travel_times, default_level):
        self.env = env
        self.lift_num = lift_num
        self.travel_times = travel_times
        self.lift_pos = default_level

    def time_taken_from_origin_to_dest(self, dest):
        time_taken = (abs(self.lift_pos - dest)) * (HEIGHT_PER_LEVEL / LIFT_SPEED)

        return time_taken
