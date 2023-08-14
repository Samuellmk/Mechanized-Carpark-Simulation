"""
simulate-carpark.py

Following the Changi mechanised carpark
195 parking lots

Algorithm:
1. Nearest First - cars are stored nearest to the lift
2. Cached Nearest First - first level is used for quick storing of vehicles 
(Potential shuttle bottleneck when caching), sort to other levels when lifts are not busy
3. Randomized spot - randomized car into slots of different levels
4. Balance levels - levels are balanced based on capacity of each level (Highest level takes the longest)

Poisson distribution arrival process
"""
import random
import simpy
from scipy.stats import poisson, expon
import numpy as np
import constants as c
from lift import Lift, create_lifts_data
from parking_lot import Parking_Lot
from shuttle import Shuttle
from graph import plot_waiting_time_retrieval

waiting_time_retrieval = {}


class Carpark:
    def __init__(self, env, parking_lots, lifts, shuttles):
        self.env = env
        self.parking_lot_resources = simpy.Resource(env, parking_lots)
        self.lifts_store = lifts
        self.shuttles_store = shuttles
        self.time_taken = {}
        self.parking_lot_list = set()

    def get_shortest_avail_travel_lot(self, lift):
        available_lots = [
            lot for lot in lift.travel_times if lot not in self.parking_lot_list
        ]
        # print("Available lots:", available_lots)
        return min(available_lots, key=lift.travel_times.get)

    def get_shortest_travel_lift(self, lift, lot):
        return lift.travel_times.get(lot)

    def check_shuttle_usage(self):
        if len(self.shuttles_store.items) == 0:
            print("No Shuttle is currently available at %.2f" % (env.now))

    def check_lift_usage(self):
        if len(self.lifts_store.items) == 0:
            print("Lifts are currently all occupied at %.2f" % (env.now))
        else:
            available_lifts = [lift.lift_num for lift in self.lifts_store.items]
            print(
                "Lifts %s are available at %.2f"
                % (", ".join(map(str, available_lifts)), env.now)
            )

    def park(self, car_id):
        # Wait for available lift
        self.check_lift_usage()
        lift = yield self.lifts_store.get()
        print(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (car_id, lift.lift_num, env.now)
        )

        # Request for shuttle
        self.check_shuttle_usage()
        shuttle = yield self.shuttles_store.get()
        # Shuttle from somewhere moves to lift position
        shuttle_time_taken = shuttle.time_taken_to_destination(lift.lift_num, lift=True)
        yield env.timeout(shuttle_time_taken)

        # Driving out from lift delay
        yield env.timeout(random.uniform(*c.DRIVE_IN_OUT))
        # Put lift back into store
        self.lifts_store.put(lift)

        # Finding the shortest available travel lot
        parking_lot_num = self.get_shortest_avail_travel_lot(lift)
        # Parking is reserved for this car
        self.parking_lot_list.add(parking_lot_num)
        # Travelling time from front of lift to parking lot
        time_taken_to_parking = lift.travel_times.get(parking_lot_num)
        yield env.timeout(time_taken_to_parking)

        print(
            "Car %d parked at parking lot %d at %.2f"
            % (car_id, parking_lot_num, env.now)
        )

        # Move shuttle back to default position
        env.process(self.moving_shuttle_back_to_default(shuttle))

        return parking_lot_num

    def exit(self, car_id, parking_lot_num, parking_lot_request):
        retrieval_time = expon.rvs(scale=1 / c.RETRIEVAL_TIME)
        print(
            "Car %d will be retrieved from parking lot %d at %.2f (+%.2f)"
            % (car_id, parking_lot_num, env.now + retrieval_time, retrieval_time)
        )

        # Wait for the retrieval time
        yield env.timeout(retrieval_time)
        time_start = env.now

        # Request for shuttle
        self.check_shuttle_usage()
        shuttle = yield self.shuttles_store.get()
        # Shuttle from somewhere moves to parking_lot
        shuttle_time_taken = shuttle.time_taken_to_destination(parking_lot_num)
        yield env.timeout(shuttle_time_taken)

        # Wait for available lift
        self.check_lift_usage()
        lift = yield self.lifts_store.get()
        print(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (car_id, lift.lift_num, env.now)
        )

        # Travelling time from parking lot to front of lift
        time_taken_to_lift = self.get_shortest_travel_lift(lift, parking_lot_num)
        yield env.timeout(time_taken_to_lift)

        # Release parking spot
        self.parking_lot_resources.release(parking_lot_request)
        self.parking_lot_list.remove(parking_lot_num)

        # Drove into the lift bay and driver drives out
        yield env.timeout(random.uniform(*c.DRIVE_IN_OUT))
        time_end = env.now
        waiting_time_retrieval[car_id] = time_end - time_start
        print("Car %d exits out of the carpark at %.2f" % (car_id, env.now))

        # Put Lift back into store
        self.lifts_store.put(lift)

        # Move shuttle back to default position
        env.process(self.moving_shuttle_back_to_default(shuttle))

    def moving_shuttle_back_to_default(self, shuttle):
        # Move shuttle back to default position
        yield env.timeout(shuttle.move_to_default_pos())
        print("Shuttle back to default position at %.2f" % (env.now))
        # Put shuttle back into store
        self.shuttles_store.put(shuttle)


def car(env, car_id, carpark):
    parking_lot_request = carpark.parking_lot_resources.request()
    yield parking_lot_request

    parking_lot_num = yield env.process(carpark.park(car_id))
    env.process(carpark.exit(car_id, parking_lot_num, parking_lot_request))


def car_arrival(env, num_of_parking, num_of_shuttle_per_level, lifts):
    carpark = Carpark(env, num_of_parking, num_of_shuttle_per_level, lifts)

    # IDs for the car
    car_id = 1
    while True:
        # Poisson distribution
        next_car = poisson.rvs(c.CAR_ARRIVAL_RATE)
        yield env.timeout(next_car)
        print(
            "Car %s arrived at the entrance of the carpark at %.2f." % (car_id, env.now)
        )
        env.process(car(env, car_id, carpark))
        car_id += 1


if __name__ == "__main__":
    env = simpy.Environment()
    np.random.seed(seed=c.RANDOM_SEEDS)

    # Create Lifts Store
    lifts_travel_data = create_lifts_data(c.LIFTS)
    lifts_store = simpy.Store(env, capacity=c.NUM_OF_LIFTS)
    for i in range(1, c.NUM_OF_LIFTS + 1):
        lifts_store.items.append(Lift(env, i, lifts_travel_data[i - 1]))

    # Create Shuttle Store
    shuttles_store = simpy.Store(env, capacity=c.NUM_OF_SHUTTLE_PER_LEVEL)
    for i in range(1, c.NUM_OF_SHUTTLE_PER_LEVEL + 1):
        shuttles_store.items.append(Shuttle(env, i))

    env.process(
        car_arrival(
            env,
            c.NUM_OF_PARKING_PER_LEVEL,
            lifts_store,
            shuttles_store,
        )
    )
    env.run(until=c.SIM_TIME)

    print("---Done---")

    plot_waiting_time_retrieval(waiting_time_retrieval)
