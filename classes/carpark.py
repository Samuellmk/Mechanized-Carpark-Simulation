import simpy
import random

from constants import *
from scipy.stats import poisson, expon
from animation.utils import (
    findCoord,
    findShuttle,
    moveToGroundLift,
    moveShuttle,
    moveLiftToPallet,
    moveOriginToLot,
    rotateVehicle,
    movePalletToLot,
    moveOutOfLift,
)


class Carpark:
    def __init__(
        self, env, total_parking_lots, parking_lots_sets, lifts, shuttles, layout
    ):
        self.env = env
        # To keep track the total amount of carpark lots available
        self.total_parking_lot_resources = total_parking_lots
        # A list of set, [<Set for level 1 cars>, ...], to keep track each level lots
        self.parking_lots_sets = parking_lots_sets
        self.lifts_store = lifts
        self.shuttles_stores = shuttles
        self.time_taken = {}
        self.parking_queue = []
        self.layout = layout

    def get_shortest_avail_travel_lot(self, lift, level):
        available_lots = [
            lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]
        ]
        # print("Available lots:", lift.travel_times)
        shortest_time_lot = min(
            available_lots, key=lambda lot: lift.travel_times[lot]["total"]
        )
        # print(shortest_time_lot)
        return shortest_time_lot

    def get_remaining_parking_lots(self):
        return (
            self.total_parking_lot_resources.capacity
            - self.total_parking_lot_resources.count
        )

    def get_parking_queue(self):
        return self.parking_queue

    def get_shortest_to_lot_lift(self, level_layout):
        # TODO: get lift that is shortest distance to the parking lift
        lift = self.lifts_store.get()
        return lift

    def check_lift_usage(self):
        if len(self.lifts_store.items) == 0:
            print("Lifts are currently all occupied at %.2f" % (self.env.now))
        else:
            available_lifts = [lift.lift_num for lift in self.lifts_store.items]
            sorted_lifts = sorted(available_lifts)
            print(
                "Lifts %s are available at %.2f"
                % (", ".join(map(str, sorted_lifts)), self.env.now)
            )

    def get_shuttle_availability(self):
        # check if which level shuttle is free
        for idx, shuttle_store in enumerate(self.shuttles_stores):
            if len(shuttle_store.items) > 0:
                return idx
        # no shuttle free, randomly select one level
        return random.randint(0, NUM_OF_LEVELS)

    def check_shuttle_usage(self, level):
        cur_shuttle = self.shuttles_stores[level].items
        if len(cur_shuttle) == 0:
            print("Shuttle is crurrently all occupied at %.2f" % (self.env.now))

    # TODO: include lift send back to ground? stay at current position?
    def park(self, vehicle):
        # To which level? Check based on shuttle
        avail_shuttle_level = self.get_shuttle_availability()

        # Wait for available lift
        self.check_lift_usage()
        lift = yield self.lifts_store.get()

        # Move Lift to ground level
        # TODO: Add lift animation
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(0)
        yield self.env.timeout(lift_time_taken_to_ground)

        # Driver Driving into the lift delay
        cur_level_layout = self.layout[avail_shuttle_level + 1]
        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        lift_coord = findCoord(cur_level_layout, lift)
        moveToGroundLift(vehicle, lift_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)

        print(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (vehicle.id, lift.lift_num, self.env.now)
        )

        # Lift Travel Time to that level
        # TODO: retrieving shuttle time while lift going up?
        lift_time_taken = lift.time_taken_from_origin_to_dest(avail_shuttle_level)
        yield self.env.timeout(lift_time_taken)

        print(
            "Car %d took lift %d and at level %d at %.2f"
            % (vehicle.id, lift.lift_num, avail_shuttle_level + 1, self.env.now)
        )

        # Request for shuttle
        self.check_shuttle_usage(avail_shuttle_level)
        shuttle = yield self.shuttles_stores[avail_shuttle_level].get()
        print(
            "Car %d is at level %d using the shuttle at %.2f"
            % (vehicle.id, avail_shuttle_level + 1, self.env.now)
        )

        # Shuttle from somewhere moves to lift position
        shuttle_time_taken = shuttle.time_taken_to_destination(lift.lift_num, lift=True)
        # Animate shuttle from current to next position
        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        moveShuttle(shuttle_sprite, shuttle_time_taken, lift_coord, lift=True)
        yield self.env.timeout(shuttle_time_taken)
        print(
            "level %d shuttle %d is ready for loading at %.2f"
            % (avail_shuttle_level + 1, shuttle.shuttle_num, self.env.now)
        )

        # Finding the shortest available travel lot
        parking_lot_num = self.get_shortest_avail_travel_lot(lift, avail_shuttle_level)
        # Parking is reserved for this car
        self.parking_lots_sets[avail_shuttle_level].add(parking_lot_num)

        # Put lift back into store - lift will stay at whichever level it is at
        self.lifts_store.put(lift)

        # Travelling time from front of the lift to parking lot
        time_taken_to_parking = lift.travel_times.get(parking_lot_num)

        moveLiftToPallet(
            vehicle, time_taken_to_parking["lift_pallet"], shuttle_sprite.pos
        )
        yield self.env.timeout(time_taken_to_parking["lift_pallet"])

        parking_coord = findCoord(cur_level_layout, parking_lot_num)
        moveOriginToLot(
            vehicle,
            shuttle_sprite,
            time_taken_to_parking["origin_lot"],
            parking_coord,
        )
        yield self.env.timeout(time_taken_to_parking["origin_lot"])

        rotateVehicle(vehicle, time_taken_to_parking["turning"], parking_coord)
        yield self.env.timeout(time_taken_to_parking["turning"])

        movePalletToLot(vehicle, time_taken_to_parking["pallet_lot"], parking_coord)
        yield self.env.timeout(time_taken_to_parking["pallet_lot"])

        print(
            "Car %d parked at parking lot %d at %.2f"
            % (vehicle.id, parking_lot_num, self.env.now)
        )

        # Move shuttle back to default position and move back shuttle to default pos
        # TODO: Might have issues when waiting for shuttle to return to default pos
        self.env.process(
            self.moving_shuttle_back_to_default(
                shuttle, shuttle_sprite, avail_shuttle_level
            )
        )

        vehicle.parking_lot = (avail_shuttle_level, parking_lot_num)

    def exit(self, vehicle, parking_lot_request):
        retrieval_time = expon.rvs(scale=1 / RETRIEVAL_TIME)
        print(
            "Car %d will be retrieved from parking lot %d at %.2f (+%.2f)"
            % (
                vehicle.id,
                vehicle.parking_lot[1],
                self.env.now + retrieval_time,
                retrieval_time,
            )
        )

        # Wait for the retrieval time
        yield self.env.timeout(retrieval_time)
        time_start = self.env.now

        # Request for shuttle
        self.check_shuttle_usage(vehicle.parking_lot[0])
        shuttle = yield self.shuttles_stores[vehicle.parking_lot[0]].get()
        print(
            "Car %d is at level %d using the shuttle"
            % (vehicle.id, vehicle.parking_lot[0] + 1)
        )

        cur_level_layout = self.layout[vehicle.parking_lot[0] + 1]
        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        parking_coord = findCoord(cur_level_layout, vehicle.parking_lot[1])

        # Shuttle from somewhere moves to parking_lot
        shuttle_time_taken = shuttle.time_taken_to_destination(vehicle.parking_lot[1])
        # Animate shuttle from current to next position
        moveShuttle(shuttle_sprite, shuttle_time_taken, parking_coord)
        yield self.env.timeout(shuttle_time_taken)

        # Wait for available lift
        self.check_lift_usage()
        # Get the closest lift
        lift = yield self.get_shortest_to_lot_lift(cur_level_layout)
        print(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (vehicle.id, lift.lift_num, self.env.now)
        )

        lift_coord = findCoord(cur_level_layout, lift)
        lift_coord_center = (lift_coord[0] + GRID_WIDTH, lift_coord[1])

        # Lift travel time to reach that level
        # TODO: Add lift animation

        lift_time_taken = lift.time_taken_from_origin_to_dest(vehicle.parking_lot[0])
        yield self.env.timeout(lift_time_taken)

        # Travelling time from parking lot to lift - concurrent for lift travel time?
        time_taken_to_lift = lift.travel_times.get(vehicle.parking_lot[1])
        print(time_taken_to_lift)

        movePalletToLot(vehicle, time_taken_to_lift["pallet_lot"], shuttle_sprite.pos)
        yield self.env.timeout(time_taken_to_lift["pallet_lot"])

        moveOriginToLot(
            vehicle, shuttle_sprite, time_taken_to_lift["pallet_lot"], lift_coord_center
        )
        yield self.env.timeout(time_taken_to_lift["pallet_lot"])

        # may need to change the function to fit both ways

        moveLiftToPallet(vehicle, time_taken_to_lift["lift_pallet"], lift_coord_center)
        yield self.env.timeout(time_taken_to_lift["lift_pallet"])

        # Lift travel time to reach ground level
        # TODO: Add lift animation
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(0)
        yield self.env.timeout(lift_time_taken_to_ground)

        # Release parking spot
        self.total_parking_lot_resources.release(parking_lot_request)
        self.parking_lots_sets[vehicle.parking_lot[0]].remove(vehicle.parking_lot[1])

        # Move shuttle back to default position and move back shuttle to default pos
        self.env.process(
            self.moving_shuttle_back_to_default(
                shuttle, shuttle_sprite, vehicle.parking_lot[0]
            )
        )
        vehicle.parking_lot = (None, None)

        # Drove into the lift bay and driver drives out
        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        moveOutOfLift(vehicle, lift_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)
        time_end = self.env.now
        # waiting_time_retrieval[vehicle.id] = time_end - time_start
        print("Car %d exits out of the carpark at %.2f" % (vehicle.id, self.env.now))

        # Put Lift back into store - lift will stay at whichever level it is at
        self.lifts_store.put(lift)

    def moving_shuttle_back_to_default(self, shuttle, shuttle_sprite, level):
        # Move shuttle back to default position
        time_taken = shuttle.move_to_default_pos()
        moveShuttle(shuttle_sprite, time_taken, shuttle_sprite.default_pos)
        yield self.env.timeout(time_taken)
        print("Shuttle back to default position at %.2f" % (self.env.now))
        # Put shuttle back into store
        self.shuttles_stores[level].put(shuttle)
