import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
import os
from simpy.util import start_delayed
import random
from scipy.stats import weibull_min, expon
from constants import *
from os.path import join
import seaborn as sns

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
    
    #duration = weibull_min.rvs(c=CAR_DURATION_K, scale=CAR_DURATION_LAMBDA) * 60
    duration = expon.rvs(scale=1/CAR_RATE)
    
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
    
    for car_arrival in car_arrival_list:
        random_times_list = generate_times(car_arrival)

        if car_arrival != 0:
            for random_time in random_times_list:
                #print(env.now, random_time)
                
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


def show_stats(carpark):
    print("=============STATISTICS=============")
    parking_dict = carpark.stats_box.waiting_stats["parking"]
    retrieval_dict = carpark.stats_box.waiting_stats["retrieval"]
    floors_occupancy = carpark.stats_box.utilization_stats["floors"]
    
    sns.set(style="whitegrid")
    fig=plt.figure(figsize=(16,8))
    gs=GridSpec(2,2) # 2 rows, 4 columns

    ax1=fig.add_subplot(gs[0,0]) # First row, first column
    ax2=fig.add_subplot(gs[0,1]) # First row, second column
    ax3=fig.add_subplot(gs[1,:]) # Second row, span column
    
    plot_waiting_time(parking_dict, "Parking", ax1)
    plot_waiting_time(retrieval_dict, "Retrieval", ax2)
    plot_floors_trend(floors_occupancy, "Level", ax3)

    plt.show()

def plot_waiting_time(wait_dict, title, ax):
    # Extract data from the waiting_times dictionary
    labels = list(wait_dict.keys())
    times = list(wait_dict.values())

    mean_waiting_time = np.mean(times)
    print(f"Mean of waiting time for Car {title.lower()}: {mean_waiting_time:.2f}")
    
    # Plot the data as a bar chart
    sns.barplot(x=labels, y=times, palette=sns.color_palette("RdBu", n_colors=7), lw=0., ax=ax)
    ax.set_xlabel("Car ID")
    ax.set_ylabel(f"Waiting Time for {title}")
    ax.set_title(f"Waiting Time for {title} of Cars")
    ax.set_xticks(np.arange(0, len(labels)+1, 30))
    ax.set_xticklabels(ax.get_xticks(), rotation = 45)
    
    plt.tight_layout()
    
def plot_floors_trend(floors, title, ax):
    times= np.arange(0, len(floors[0]) * 5, 5)
    
    for idx,floor in enumerate(floors):
        label = f"Floor {idx+1}"
        sns.lineplot(x=times, y=floor, ax=ax, label=label)
        
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_xlabel("Time (Interval of 5 mins)")
    ax.set_ylabel(f"Parking Occupancy/Level")
    ax.set_title(f"{title} {idx+1}")
    ax.set_xticklabels(ax.get_xticks(), rotation = 45)
    ax.legend()


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
        
def collect_floor(env, carpark):
    floors = carpark.stats_box.utilization_stats["floors"]
    
    while True:
        for lvl in range(NUM_OF_LEVELS):
            cars_per_lvl = NUM_OF_PARKING_PER_LEVEL - carpark.available_parking_lots_per_level[lvl]
            floors[lvl].append(cars_per_lvl / NUM_OF_PARKING_PER_LEVEL)
            
        yield env.timeout(DATA_COLLECTION_INTERVAL)
