import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import os
from simpy.util import start_delayed
import random
from scipy.stats import poisson, expon
from constants import *
from os.path import join

from classes.vehicle import Vehicle


def run(env, renderer, carpark):
    parking_lot_request = carpark.total_parking_lot_resources.request()
    yield parking_lot_request
    vehicle = carpark.parking_queue.pop(0)

    renderer.add(vehicle)
    yield env.process(carpark.park(vehicle))

    retrieval_time = expon.rvs(scale=RETRIEVAL_TIME)
    print(
        "Car %d will be retrieved from parking lot %d at %.2f (+%.2f)"
        % (
            vehicle.id,
            vehicle.parking_lot[1],
            env.now + retrieval_time,
            retrieval_time,
        )
    )
    # Wait for the retrieval time
    yield start_delayed(
        env, carpark.exit(vehicle, parking_lot_request), delay=retrieval_time
    )


def vehicle_arrival(env, renderer, carpark, num_cars):
    files_list = os.listdir(join("assets", "Cars"))
    car_names = [os.path.splitext(file)[0] for file in files_list]

    vehicle_placement = ((WIDTH // 2) - 24, 680) # 24 = half the width of vehicle sprite
    for car_id in range(1, num_cars + 1):
        car_name = random.choice(car_names)
        vehicle = Vehicle(vehicle_placement[0], vehicle_placement[1], env, id=car_id, car_png=car_name)
        carpark.parking_queue.append(vehicle)
        carpark.stats_box.stats["Cars Waiting"] += 1

        print(
            "Car %d arrived at the entrance of the carpark at %.2f." % (car_id, env.now)
        )
        env.process(run(env, renderer, carpark))

        next_car = round(expon.rvs(scale=1/CAR_ARRIVAL_RATE), 2)
        print(
            "Next Car %d arrived at the entrance of the carpark at %.2f (+%.2f)."
            % (car_id + 1, env.now + next_car, next_car)
        )
        yield env.timeout(next_car)


def print_stats(env, carpark):
    print("=============STATISTICS=============")
    print(
        "%d out of %d carpark lots remaining"
        % (
            carpark.get_remaining_parking_lots(),
            NUM_OF_PARKING_PER_LEVEL * NUM_OF_LEVELS,
        )
    )

    cars_queued_num = len(carpark.get_parking_queue())
    cars_queued = ", ".join(str(car_id) for car_id in carpark.get_parking_queue())

    print("%d cars waiting for carpark lots %s " % (cars_queued_num, cars_queued))

    # plot_waiting_time_retrieval(waiting_time_retrieval)


def plot_waiting_time_retrieval(waiting_times):
    # Extract data from the waiting_times dictionary
    labels = list(waiting_times.keys())
    times = list(waiting_times.values())

    mean_waiting_time = np.mean(times)
    print("mean of waiting_time for car retrieval: %.2f" % mean_waiting_time)

    # Plot the data as a bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(labels, times, color="green")
    plt.xlabel("Car ID")
    plt.ylabel("Waiting Time for Retrieval")
    plt.title("Waiting Time for Retrieval of Cars")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Show the plot
    plt.show()


# v_lot is wrt to x axis
# a_lot is the actual lot number
def lift_wrt_lot(lift_pos, v_lot, a_lot, turning):
    time_taken_from_lift_to_pallet = round(WIDTH_PER_CAR / PALLET_SPEED, 2)

    time_taken_from_origin_to_lot = round(
        (WIDTH_PER_CAR * (abs(lift_pos - v_lot))) / SHUTTLE_SPEED, 2
    )

    # Rotate vehicle
    time_taken_to_rotate = round(180 / (ROTARY * 360), 2)

    # Pallet to lot
    time_taken_from_pallet_to_lot = round(WIDTH_PER_CAR / PALLET_SPEED, 2)

    time_takens = {
        "lift_pallet": time_taken_from_lift_to_pallet,  # lift to pallet
        "pallet_lot": time_taken_from_pallet_to_lot,  # pallet to lot
        "origin_lot": time_taken_from_origin_to_lot,  # origin to lot
        "turning": 0,
    }

    # print("--------------")
    # print("%.2f time taken for lift to pallet" % time_taken_from_lift_to_pallet)
    # print(
    #     "%.2f time taken to travel %.2fm"
    #     % (
    #         time_taken_from_origin_to_lot,
    #         WIDTH_PER_CAR * (abs(lift_pos- v_lot)),
    #     )
    # )
    if turning:
        time_takens["turning"] = time_taken_to_rotate
        # print("%.2f time taken to rotate car" % time_taken_to_rotate)
    # print("%.2f time taken for pallet to lot" % time_taken_from_pallet_to_lot)

    total = 0
    for value in time_takens.values():
        total += value
    time_takens["total"] = round(total, 2)

    return time_takens


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


def set_stat_time(env, stats_box):
    while True:
        stats_box.stats["Tick"] = round(env.now, 2)
        yield env.timeout(0.1)
