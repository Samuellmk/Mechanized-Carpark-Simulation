import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from simpy.util import start_delayed
import random
from scipy.stats import weibull_min, expon
from constants import *
from os.path import join

from classes.vehicle import Vehicle

def process_car_arrival_csv():
    df = pd.read_csv(join("data", "morning.csv"))
    return df["car_arrival_rate"].astype(int).tolist()

def generate_times(car_arrival):
    total_of_times = []
    end_range = 100
    for _ in range(car_arrival):
        time = random.randint(0, end_range)
        total_of_times.append(time / 100)
        end_range -= time
    return total_of_times

def run(env, renderer, carpark, delay):
    # Log waiting time - START
    yield env.timeout(delay)
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
    duration = 5
    print(
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


def vehicle_arrival(env, renderer, carpark):
    files_list = os.listdir(join("assets", "Cars"))
    car_names = [os.path.splitext(file)[0] for file in files_list]
    vehicle_placement = (
        (WIDTH - 50),
        HEIGHT - 2 * STATS_HEIGHT - 5,
    )  # 24 = half the width of vehicle sprite
    
    car_arrival_list = process_car_arrival_csv()    
    car_id = 1
    
    for idx, car_arrival in enumerate(car_arrival_list):
        random_times_list = generate_times(car_arrival)

        if car_arrival != 0:
            for random_time in random_times_list:
                print(env.now, random_time)
                
                car_name = random.choice(car_names)
                vehicle = Vehicle(
                    vehicle_placement[0], vehicle_placement[1], env, id=car_id, car_png=car_name
                )
                carpark.parking_queue.append(vehicle)
                carpark.stats_box.stats["Cars Waiting"] += 1

                print(
                    "Car %d arrived at the entrance of the carpark at %.2f." % (car_id, env.now)
                )
                env.process(run(env, renderer, carpark, random_time))
                
                car_id += 1
        
        yield env.timeout(1)
        
    print("Done")


def show_stats(carpark):
    print("=============STATISTICS=============")
    parking_dict = carpark.stats_box.waiting_stats["parking"]
    retrieval_dict = carpark.stats_box.waiting_stats["retrieval"]
    plot_waiting_time_retrieval(parking_dict)
    #plot_waiting_time_retrieval(retrieval_dict)


def plot_waiting_time_retrieval(wait_dict):
    # Extract data from the waiting_times dictionary
    labels = list(wait_dict.keys())
    times = list(wait_dict.values())

    mean_waiting_time = np.mean(times)
    print("Mean of waiting_time for car retrieval: %.2f" % mean_waiting_time)
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
