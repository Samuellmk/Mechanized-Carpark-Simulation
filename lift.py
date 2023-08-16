"""
This is to get all the distances stored into each Lift classes,
as well as the availability of parking spaces for each lot
"""
import constants as c
import simpy


class Lift:
    def __init__(self, env, lift_num, travel_times):
        self.env = env
        self.lift_num = lift_num
        self.travel_times = travel_times
        self.lift_pos = 0

    def time_taken_from_origin_to_dest(self, dest):
        time_taken = (abs(self.lift_pos - dest)) * (c.HEIGHT_PER_LEVEL / c.LIFT_SPEED)
        self.lift_pos = dest
        return time_taken


# v_lot is wrt to x axis
# a_lot is the actual lot number
def lift_wrt_lot(lift_pos, v_lot, a_lot, turning):
    time_taken_from_lift_to_pallet = c.WIDTH_PER_CAR / c.PALLET_SPEED

    time_taken_from_origin_to_lot = (
        c.WIDTH_PER_CAR * (abs(lift_pos - v_lot))
    ) / c.SHUTTLE_SPEED

    # Rotate vehicle
    time_taken_to_rotate = 180 / (c.ROTARY * 360)

    # Pallet to lot
    time_taken_from_pallet_to_lot = c.WIDTH_PER_CAR / c.PALLET_SPEED

    total_time = (
        time_taken_from_lift_to_pallet
        + time_taken_from_origin_to_lot
        + time_taken_from_pallet_to_lot
    )

    # print("--------------")
    # print("%.2f time taken for lift to pallet" % time_taken_from_lift_to_pallet)
    # print(
    #     "%.2f time taken to travel %.2fm"
    #     % (
    #         time_taken_from_origin_to_lot,
    #         c.WIDTH_PER_CAR * (abs(lift_pos- v_lot)),
    #     )
    # )
    if turning:
        total_time += time_taken_to_rotate
        # print("%.2f time taken to rotate car" % time_taken_to_rotate)
    # print("%.2f time taken for pallet to lot" % time_taken_from_pallet_to_lot)
    return round(total_time, 2)


def create_lifts_data(lifts_pos):
    lifts = []
    for lift in lifts_pos:
        cur_lots = {}
        # North part of carpark (v_lot same as a_lot)
        for v_lot in range(1, 27):
            cur_lots[v_lot] = lift_wrt_lot(lift, v_lot, v_lot, True)

        # South-West part of carpark
        a_lot = 27
        for v_lot in range(1, 8):
            cur_lots[a_lot] = lift_wrt_lot(lift, v_lot, a_lot, False)
            a_lot += 1

        # South-East part of carpark
        a_lot = 34
        for v_lot in range(20, 26):
            cur_lots[a_lot] = lift_wrt_lot(lift, v_lot, a_lot, False)
            a_lot += 1

        lifts.append(cur_lots)

    return lifts
