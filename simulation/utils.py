import pandas as pd
import os
from simpy.util import start_delayed
import random
from scipy.stats import expon
from constants import *
from os.path import join

from classes.vehicle import Vehicle
from animation.popup import Popup

import logging


def process_car_arrival_csv():
    df = pd.read_csv(join("data", "slices", "6-14 Hours.csv"))
    return df["car_arrival_rate"].tolist()


def generate_times(car_arrival, logger):
    times = []

    for _ in range(car_arrival):
        # Generate a random time between 0 and the remaining time
        time_interval = round(random.uniform(0.0, 1.0), 2)
        times.append(time_interval)

    return times


def run(env, renderer, carpark, car_id, delay, logger):
    yield env.timeout(delay)
    logger.info(
        "Car %d arrived at the entrance of the carpark at %.2f." % (car_id, env.now)
    )
    # Log waiting time - START
    time_start = env.now

    parking_lot_request = carpark.total_parking_lot_resources.request()
    yield parking_lot_request
    vehicle = carpark.parking_queue.pop(0)

    renderer.add(vehicle)
    yield env.process(carpark.park(vehicle))

    # Log waiting time - END
    time_end = env.now
    carpark.stats_box.waiting_stats["parking"][vehicle.id] = round(
        time_end - time_start, 2
    )

    # duration = weibull_min.rvs(c=CAR_DURATION_K, scale=CAR_DURATION_LAMBDA) * 60
    duration = expon.rvs(scale=1 / CAR_RATE)
    vehicle.popup.set_text("exiting time", round(env.now + duration, 2))
    logger.info(
        "Car %d will be retrieved from parking lot %d at %.2f (+%.2f)"
        % (
            vehicle.id,
            vehicle.parking_lot[1],
            env.now + duration,
            duration,
        )
    )

    # Wait for the retrieval time
    yield start_delayed(env, carpark.exit(vehicle, parking_lot_request), delay=duration)


def vehicle_arrival(env, renderer, carpark, logger):
    files_list = os.listdir(join("assets", "Cars"))
    car_names = [os.path.splitext(file)[0] for file in files_list]
    vehicle_placement = (
        (WIDTH - 50),
        HEIGHT - 2 * STATS_HEIGHT - 5,
    )  # 24 = half the width of vehicle sprite

    car_arrival_list = process_car_arrival_csv()
    car_id = 1

    for car_arrival in car_arrival_list:
        logger.warn(f"Time now: {env.now}")
        if car_arrival != 0:
            random_times_list = generate_times(car_arrival, logger)
            formatted_list = ", ".join(map(str, random_times_list))
            logger.info(f"Random list: {formatted_list}")
            delay = 0.0
            for random_time in random_times_list:
                popup = Popup(car_id)

                car_name = random.choice(car_names)
                vehicle = Vehicle(
                    vehicle_placement[0],
                    vehicle_placement[1],
                    env,
                    id=car_id,
                    car_png=car_name,
                    popup=popup,
                )
                carpark.parking_queue.append(vehicle)
                carpark.stats_box.stats["Cars Waiting"] += 1

                env.process(run(env, renderer, carpark, car_id, random_time, logger))
                car_id += 1

        yield env.timeout(1)
    logger.info("--No more incoming vehicles--")


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

    # logger.info("--------------")
    # logger.info("%.2f time taken for lift to pallet" % time_taken_from_lift_to_pallet)
    # logger.info(
    #     "%.2f time taken to travel %.2fm"
    #     % (
    #         time_taken_from_origin_to_lot,
    #         WIDTH_PER_CAR * (abs(lift_pos- v_lot)),
    #     )
    # )
    if turning:
        time_takens["turning"] = time_taken_to_rotate
        # logger.info("%.2f time taken to rotate car" % time_taken_to_rotate)
    # logger.info("%.2f time taken for pallet to lot" % time_taken_from_pallet_to_lot)

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


def collect_floor(env, carpark):
    floors = carpark.stats_box.utilization_stats["floors"]

    while True:
        for lvl in range(NUM_OF_LEVELS):
            cars_per_lvl = (
                NUM_OF_PARKING_PER_LEVEL - carpark.available_parking_lots_per_level[lvl]
            )
            floors[lvl].append(cars_per_lvl / NUM_OF_PARKING_PER_LEVEL)

        yield env.timeout(DATA_COLLECTION_INTERVAL)


def logging_setup(type):
    # Create a logger
    logger = logging.getLogger(f"my_logger - {type}")
    logger.setLevel(logging.DEBUG)

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create a handler for stdout (console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create a handler for a log file
    file_handler = logging.FileHandler(f"my_logger - {type}")
    file_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
