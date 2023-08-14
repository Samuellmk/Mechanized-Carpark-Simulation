import constants as c


class Shuttle:
    def __init__(self, env, shuttle_num):
        self.env = env
        self.shuttle_num = shuttle_num
        self.cur_pos = 13

    def time_taken_to_destination(self, destination, lift=False):
        if lift:
            destination = c.LIFTS[destination - 1]
        else:
            # Using the north carpark slot as reference instead
            if destination >= 27 and destination <= 33:
                destination -= 26
            elif destination >= 34 and destination <= 39:
                destination -= 14

        distance = c.WIDTH_PER_CAR * abs(self.cur_pos - destination)
        time_taken = distance / c.SHUTTLE_SPEED

        self.cur_pos = destination

        return time_taken  # min

    def move_to_default_pos(self):
        return self.time_taken_to_destination(13)
