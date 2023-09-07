"""
simulate-carpark.py

Following the Changi mechanised carpark
195 parking lots

Algorithm:
[✓] 1. Nearest First - cars are stored nearest to the lift
[ ] 2. Cached Nearest First - first level is used for quick storing of vehicles 
(Potential shuttle bottleneck when caching), sort to other levels when lifts are not busy
[ ] 3. Randomized spot - randomized car into slots of different levels
[ ] 4. Balance levels - levels are balanced based on capacity of each level (Highest level takes the longest)

Poisson distribution arrival process
"""
import random
import simpy
import pandas as pd
from scipy.stats import poisson, expon
import numpy as np
import constants as c
from classes.lift import Lift, create_lifts_data
from classes.parking_lot import Parking_Lot
from classes.shuttle import Shuttle
from graph import plot_waiting_time_retrieval

waiting_time_retrieval = {}
# Will add more data to this dataframe in the future
events_df = pd.DataFrame(columns=["Car ID", "Park Time", "Exit Time"])


def car(env, carpark):
    parking_lot_request = carpark.total_parking_lot_resources.request()
    yield parking_lot_request
    car_id = carpark.parking_queue.pop(0)

    parking_lot_num, level = yield env.process(carpark.park(car_id))
    env.process(carpark.exit(car_id, parking_lot_num, parking_lot_request, level))


if __name__ == "__main__":
    env = simpy.Environment()
    np.random.seed(seed=c.RANDOM_SEEDS)

    env.process(car_arrival(env, carpark, c.CAR_NUMBER))
    env.run()

    print("---Done---")

    # print_stats(env, carpark)
