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
from lift import Lift, create_lifts_data
from parking_lot import Parking_Lot
from shuttle import Shuttle
from graph import plot_waiting_time_retrieval, plot_timeline_each_car

waiting_time_retrieval = {}
# Will add more data to this dataframe in the future
events_df = pd.DataFrame(columns=["Car ID", "Park Time", "Exit Time"])


class Carpark:
    def __init__(self, env, total_parking_lots, parking_lots_sets, lifts, shuttles):
        self.env = env
        # To keep track the total amount of carpark lots available
        self.total_parking_lot_resources = total_parking_lots
        # A list of set, [<Set for level 1 cars>, ...], to keep track each level lots
        self.parking_lots_sets = parking_lots_sets
        self.lifts_store = lifts
        self.shuttles_stores = shuttles
        self.time_taken = {}
        self.parking_queue = []

    def get_shortest_avail_travel_lot(self, lift, level):
        available_lots = [
            lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]
        ]
        # print("Available lots:", available_lots)
        return min(available_lots, key=lift.travel_times.get)

    def get_remaining_parking_lots(self):
        return (
            self.total_parking_lot_resources.capacity
            - self.total_parking_lot_resources.count
        )

    def get_parking_queue(self):
        return self.parking_queue

    def get_shortest_travel_lift(self, lift, lot):
        return lift.travel_times.get(lot)

    def check_lift_usage(self):
        if len(self.lifts_store.items) == 0:
            print("Lifts are currently all occupied at %.2f" % (env.now))
        else:
            available_lifts = [lift.lift_num for lift in self.lifts_store.items]
            sorted_lifts = sorted(available_lifts)
            print(
                "Lifts %s are available at %.2f"
                % (", ".join(map(str, sorted_lifts)), env.now)
            )

    def get_shuttle_availability(self):
        # check if which level shuttle is free
        for idx, shuttle_store in enumerate(self.shuttles_stores):
            if len(shuttle_store.items) > 0:
                return idx
        # no shuttle free, randomly select one level
        return random.randint(0, c.NUM_OF_LEVELS)

    def check_shuttle_usage(self, level):
        cur_shuttle = self.shuttles_stores[level].items
        if len(cur_shuttle) == 0:
            print("Shuttle is crurrently all occupied at %.2f" % (env.now))

    # TODO: include lift send back to ground? stay at current position?
    def park(self, car_id):
        # To which level? Check based on shuttle
        avail_shuttle_level = self.get_shuttle_availability()

        # Wait for available lift
        self.check_lift_usage()
        lift = yield self.lifts_store.get()

        # Move Lift to ground level
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(0)
        yield env.timeout(lift_time_taken_to_ground)

        # Driver Driving into the lift delay
        yield env.timeout(random.uniform(*c.DRIVE_IN_OUT))

        # Lift Travel Time to that level
        # TODO: retrieving shuttle time while lift going up?
        lift_time_taken = lift.time_taken_from_origin_to_dest(avail_shuttle_level)
        yield env.timeout(lift_time_taken)

        print(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (car_id, lift.lift_num, env.now)
        )

        # Request for shuttle
        self.check_shuttle_usage(avail_shuttle_level)
        shuttle = yield self.shuttles_stores[avail_shuttle_level].get()
        print(
            "Car %d is at level %d using the shuttle"
            % (car_id, avail_shuttle_level + 1)
        )

        # Shuttle from somewhere moves to lift position
        shuttle_time_taken = shuttle.time_taken_to_destination(lift.lift_num, lift=True)
        yield env.timeout(shuttle_time_taken)

        # Finding the shortest available travel lot
        parking_lot_num = self.get_shortest_avail_travel_lot(lift, avail_shuttle_level)
        # Parking is reserved for this car
        self.parking_lots_sets[avail_shuttle_level].add(parking_lot_num)

        # Put lift back into store - lift will stay at whichever level it is at
        self.lifts_store.put(lift)

        # Travelling time from front of the lift to parking lot
        time_taken_to_parking = lift.travel_times.get(parking_lot_num)
        yield env.timeout(time_taken_to_parking)

        print(
            "Car %d parked at parking lot %d at %.2f"
            % (car_id, parking_lot_num, env.now)
        )

        # Move shuttle back to default position and move back shuttle to default pos
        # TODO: Might have issues when waiting for shuttle to return to default pos
        env.process(self.moving_shuttle_back_to_default(shuttle, avail_shuttle_level))

        return parking_lot_num, avail_shuttle_level

    # TODO: park per level basis - include more logic for lift to certain level, etc.
    def exit(self, car_id, parking_lot_num, parking_lot_request, level):
        retrieval_time = expon.rvs(scale=1 / c.RETRIEVAL_TIME)
        print(
            "Car %d will be retrieved from parking lot %d at %.2f (+%.2f)"
            % (car_id, parking_lot_num, env.now + retrieval_time, retrieval_time)
        )

        # Wait for the retrieval time
        yield env.timeout(retrieval_time)
        time_start = env.now

        # Request for shuttle
        self.check_shuttle_usage(level)
        shuttle = yield self.shuttles_stores[level].get()
        print("Car %d is at level %d using the shuttle" % (car_id, level + 1))

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

        # Lift travel time to reach that level
        lift_time_taken = lift.time_taken_from_origin_to_dest(level)
        yield env.timeout(lift_time_taken)

        # Travelling time from parking lot to lift - concurrent for lift travel time?
        time_taken_to_lift = self.get_shortest_travel_lift(lift, parking_lot_num)
        yield env.timeout(time_taken_to_lift)

        # Lift travel time to reach ground level
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(0)
        yield env.timeout(lift_time_taken_to_ground)

        # Release parking spot
        self.total_parking_lot_resources.release(parking_lot_request)
        self.parking_lots_sets[level].remove(parking_lot_num)

        # Move shuttle back to default position and move back shuttle to default pos
        env.process(self.moving_shuttle_back_to_default(shuttle, level))

        # Drove into the lift bay and driver drives out
        yield env.timeout(random.uniform(*c.DRIVE_IN_OUT))
        time_end = env.now
        waiting_time_retrieval[car_id] = time_end - time_start
        print("Car %d exits out of the carpark at %.2f" % (car_id, env.now))

        # Put Lift back into store - lift will stay at whichever level it is at
        self.lifts_store.put(lift)

    def moving_shuttle_back_to_default(self, shuttle, level):
        # Move shuttle back to default position
        yield env.timeout(shuttle.move_to_default_pos())
        print("Shuttle back to default position at %.2f" % (env.now))
        # Put shuttle back into store
        self.shuttles_stores[level].put(shuttle)


def car(env, carpark):
    parking_lot_request = carpark.total_parking_lot_resources.request()
    yield parking_lot_request
    car_id = carpark.parking_queue.pop(0)

    parking_lot_num, level = yield env.process(carpark.park(car_id))
    env.process(carpark.exit(car_id, parking_lot_num, parking_lot_request, level))


def car_arrival(env, carpark, num_cars):
    for car_id in range(1, num_cars + 1):
        # Poisson distribution
        carpark.parking_queue.append(car_id)
        print(
            "Car %s arrived at the entrance of the carpark at %.2f." % (car_id, env.now)
        )
        env.process(car(env, carpark))

        next_car = poisson.rvs(c.CAR_ARRIVAL_RATE)
        yield env.timeout(next_car)


def print_stats(env, carpark):
    print("=============STATISTICS=============")
    print(
        "%d out of %d carpark lots remaining"
        % (
            carpark.get_remaining_parking_lots(),
            c.NUM_OF_PARKING_PER_LEVEL * c.NUM_OF_LEVELS,
        )
    )

    cars_queued_num = len(carpark.get_parking_queue())
    cars_queued = ", ".join(str(car_id) for car_id in carpark.get_parking_queue())

    print("%d cars waiting for carpark lots %s " % (cars_queued_num, cars_queued))

    # plot_waiting_time_retrieval(waiting_time_retrieval)

    # plot_timeline_each_car(events)


if __name__ == "__main__":
    env = simpy.Environment()
    np.random.seed(seed=c.RANDOM_SEEDS)

    # Create Lifts Store
    lifts_travel_data = create_lifts_data(c.LIFTS)
    lifts_store = simpy.Store(env, capacity=c.NUM_OF_LIFTS)
    for i in range(1, c.NUM_OF_LIFTS + 1):
        lifts_store.items.append(Lift(env, i, lifts_travel_data[i - 1]))

    parking_lots_sets = []
    shuttles_stores = []
    for _ in range(c.NUM_OF_LEVELS):
        # Create Shuttle Store
        shuttles_store = simpy.Store(env, capacity=c.NUM_OF_SHUTTLE_PER_LEVEL)
        for i in range(1, c.NUM_OF_SHUTTLE_PER_LEVEL + 1):
            shuttles_store.items.append(Shuttle(env, i))
        shuttles_stores.append(shuttles_store)

        # Create Parking lot resources
        parking_lots_sets.append(set())

    total_parking_lots = simpy.Resource(
        env, c.NUM_OF_PARKING_PER_LEVEL * c.NUM_OF_LEVELS
    )
    carpark = Carpark(
        env, total_parking_lots, parking_lots_sets, lifts_store, shuttles_stores
    )

    env.process(car_arrival(env, carpark, c.CAR_NUMBER))
    env.run()

    print("---Done---")

    print_stats(env, carpark)
