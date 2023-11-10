import pandas as pd
import os
from simpy.util import start_delayed
import random
from scipy.stats import weibull_min
from constants import *
from os.path import join

from classes.vehicle import Vehicle
from animation.popup import Popup

import logging
import datetime


def process_car_arrival_csv():
    period = os.environ["PERIOD"]
    df = pd.read_csv(join("data", "slices", period))
    # df = pd.read_csv(join("data", "slices", "6-14 Hours.csv"))
    # df = pd.read_csv(join("data", "slices", "test.csv"))
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
    yield env.process(carpark.park(vehicle, time_start))

    duration = weibull_min.rvs(c=CAR_DURATION_SHAPE, scale=CAR_DURATION_SCALE) * 60
    # duration = expon.rvs(scale=1 / CAR_RATE)
    # duration = 0.7  # 0.7  # 0.67  # 0.65  # 0.6  # 0.46  # 0.42  # 0.4  # 0.35  # 0.3
    # duration = random.randint(1, 2)
    # duration = 15
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

    buffer = duration - CALL_FOR_RETRIEVAL
    buffer_duration = env.timeout(buffer)
    if carpark.policy == "Cache" and vehicle.parking_lot[0] == 0:
        # Drivers will alert 10 mins before collecting their vehicles
        move_process = env.process(
            carpark.move_vehicle_on_idle_shuttle(vehicle, parking_lot_request)
        )
        yield buffer_duration | move_process

        if not move_process.triggered:
            move_process.interrupt()
        else:
            yield buffer_duration
            yield env.process(
                move_ground_to_exit(env, carpark, vehicle, parking_lot_request)
            )

    else:
        yield buffer_duration
        yield env.process(
            move_ground_to_exit(env, carpark, vehicle, parking_lot_request)
        )


def move_ground_to_exit(env, carpark, vehicle, parking_lot_request):
    remain_time = env.timeout(CALL_FOR_RETRIEVAL)
    remain_time_end = env.now + CALL_FOR_RETRIEVAL

    if vehicle.parking_lot[0] > 0:
        print("Car %d: Driver called for retrieval at %.2f" % (vehicle.id, env.now))
        ground_time_process = env.process(
            carpark.move_to_ground_level(vehicle, remain_time_end)
        )

        yield ground_time_process

    yield remain_time
    env.process(carpark.exit(vehicle, parking_lot_request))


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
        # logger.warn(f"Time now: {env.now}")
        if car_arrival != 0:
            random_times_list = generate_times(car_arrival, logger)
            formatted_list = ", ".join(map(str, random_times_list))
            logger.info(f"Random list: {formatted_list}")

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
def lift_wrt_lot(pos, v_lot, a_lot, turning):
    time_taken_from_lift_to_pallet = round(WIDTH_PER_CAR / PALLET_SPEED, 2)

    time_taken_from_origin_to_lot = round(
        (WIDTH_PER_CAR * (abs(pos - v_lot))) / SHUTTLE_SPEED, 2
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
    #         WIDTH_PER_CAR * (abs(pos- v_lot)),
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


def create_lifts_data(lifts_pos, cache=False):
    lifts = []
    for lift in lifts_pos:
        cur_lots = {}
        # North part of carpark (v_lot same as a_lot)
        for v_lot in range(1, 27):
            cur_lots[v_lot] = lift_wrt_lot(lift, v_lot, v_lot, True)

        # South-West part of carpark
        range_end = 5 if cache else 8  # for cache
        a_lot = 27
        for v_lot in range(1, range_end):
            cur_lots[a_lot] = lift_wrt_lot(lift, v_lot, a_lot, True)
            a_lot += 1

        # South-East part of carpark
        a_lot = 34
        for v_lot in range(20, 26):
            cur_lots[a_lot] = lift_wrt_lot(lift, v_lot, a_lot, True)
            a_lot += 1

        lifts.append(cur_lots)

    return lifts


def collect_floor(env, carpark, instance_type):
    floors = carpark.stats_box.utilization_stats["floors"]

    isCache = True if instance_type == "Cache" else False

    while True:
        for lvl in range(NUM_OF_LEVELS):
            parking_per_level = NUM_OF_PARKING_PER_LEVEL
            if lvl == 0 and isCache:
                parking_per_level = NUM_OF_PARKING_LOBBY
            cars_per_lvl = (
                parking_per_level - carpark.available_parking_lots_per_level[lvl]
            )
            floors[lvl].append(cars_per_lvl / parking_per_level)

        yield env.timeout(DATA_COLLECTION_INTERVAL)


def logging_setup(type):
    # Create a logger

    logger = logging.getLogger(f"{type}")
    logger.setLevel(logging.DEBUG)

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create a handler for stdout (console)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Create a handler for a log file
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_handler = logging.FileHandler(join("logs", f"{type}_{timestamp}.log"))
    file_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
