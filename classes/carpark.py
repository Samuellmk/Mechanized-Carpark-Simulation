import random

from constants import *
from animation.utils import (
    findCoord,
    findShuttle,
    moveIntoGroundLift,
    moveShuttle,
    moveLiftToPallet,
    moveOriginToLot,
    rotateVehicle,
    movePalletToLot,
    moveOutOfLift,
    moveLift,
    findGroundLiftCoord,
)

"""
Algorithm:
[✓] 1. Nearest First - cars are stored nearest to the lift
[✓] 2. Randomized spot - randomized car into slots of different levels
[✓] 3. Balance levels - levels are balanced based on capacity of each level (Highest level takes the longest)
[ ] 4. Cached Nearest First - first level is used for quick storing of vehicles 
(Potential shuttle bottleneck when caching), sort to other levels when lifts are not busy
"""


class Carpark:
    def __init__(
        self,
        env,
        total_parking_lots,
        parking_lots_sets,
        lifts,
        shuttles,
        layout,
        stats_box,
        logger,
    ):
        self.env = env
        # To keep track the total amount of carpark lots available
        self.total_parking_lot_resources = total_parking_lots
        # A list of set, [<Set for level 1 cars>, ...], to keep track each level lots
        self.parking_lots_sets = parking_lots_sets
        self.available_parking_lots_per_level = [
            NUM_OF_PARKING_PER_LEVEL
        ] * NUM_OF_LEVELS
        self.lifts_store = lifts
        self.shuttles_stores = shuttles
        self.time_taken = {}
        self.parking_queue = []
        self.layout = layout
        self.shuttle_available_event = env.event()
        self.stats_box = stats_box
        self.policy = 0
        self.logger = logger

    def get_shortest_avail_travel_lot(self, lift, level):
        available_lots = [
            lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]
        ]
        # self.logger.info("Available lots:", available_lots)
        shortest_time_lot = min(
            available_lots, key=lambda lot: lift.travel_times[lot]["total"]
        )
        # self.logger.info(shortest_time_lot)
        return shortest_time_lot

    def random_parking_lot(self, lift, level):
        available_lots = [
            lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]
        ]
        random_parking = random.choice(available_lots)
        return random_parking

    def get_remaining_parking_lots(self):
        return (
            self.total_parking_lot_resources.capacity
            - self.total_parking_lot_resources.count
        )

    def get_parking_queue(self):
        return self.parking_queue

    def get_shortest_to_lot_avail_lift(self, vehicle, level_layout):
        floor_num, parking_num = vehicle

        lift_num = self.get_shortest_to_lot_lift(level_layout, parking_num)
        while lift_num == None:
            lift_num = self.get_shortest_to_lot_lift(level_layout, parking_num)
            yield self.env.timeout(0.01)
            self.logger.info(
                f"Shuttle availability, {self.shuttles_stores[floor_num].items}"
            )

        # Request for shuttle
        # self.check_shuttle_usage(vehicle.parking_lot[0])
        shuttle = yield self.shuttles_stores[floor_num].get()

        return lift_num, shuttle

    def get_shortest_to_lot_lift(self, level_layout, parking_lot_num):
        min_total = float("inf")
        min_lift = None

        # Iterate through the list of dictionaries
        for lift in self.lifts_store.items:
            travel_times = lift.travel_times
            total_time = travel_times[parking_lot_num]["total"]

            if travel_times[parking_lot_num]["turning"] > 0:
                total_time -= travel_times[parking_lot_num]["turning"]

            if total_time < min_total:
                min_total = total_time
                min_lift = lift.lift_num

        return min_lift

    def check_lift_usage(self, car_id):
        if len(self.lifts_store.items) == 0:
            self.logger.info(
                "Car %d - Lifts are currently all occupied at %.2f"
                % (car_id, self.env.now)
            )
        else:
            available_lifts = [lift.lift_num for lift in self.lifts_store.items]
            sorted_lifts = sorted(available_lifts)
            self.logger.info(
                "Lifts %s are available at %.2f"
                % (", ".join(map(str, sorted_lifts)), self.env.now)
            )

    def check_shuttle_availability(self):
        # self.logger.info("---------")
        # for idx, shuttle_store in enumerate(self.shuttles_stores):
        #     self.logger.info(
        #         "floor %d: %d left" % (idx, self.available_parking_lots_per_level[idx])
        #     )

        # for shuttle_store in self.shuttles_stores:
        #     self.logger.info(shuttle_store.items)
        # self.logger.info("---------")
        for idx, shuttle_store in enumerate(self.shuttles_stores):
            if (
                len(shuttle_store.items) > 0
                and self.available_parking_lots_per_level[idx] > 0
            ):
                self.available_parking_lots_per_level[idx] -= 1
                return idx

    def get_shuttle_level_availability(self):
        # check if which level shuttle is free
        # Possible deadlock when car wants to come out but lift is full

        floor_level = self.check_shuttle_availability()
        while floor_level == None:
            yield self.shuttle_available_event
            floor_level = self.check_shuttle_availability()

            if floor_level is not None:
                break

        # Request for shuttle
        # self.check_shuttle_usage(avail_shuttle_level)
        return floor_level

    def check_shuttle_usage(self, level):
        cur_shuttle = self.shuttles_stores[level].items
        if len(cur_shuttle) == 0:
            self.logger.info(
                "Level %d's Shuttle is currently all occupied at %.2f"
                % (level + 1, self.env.now)
            )

    def park(self, vehicle):
        # To which level? Check based on shuttle and available level

        if self.policy == "Nearest-First":
            avail_shuttle_level, shuttle = yield self.env.process(
                self.get_shuttle_level_availability()
            )  # index 0

        elif self.policy == "Randomised":
            avail_shuttle_level = random.randint(0, NUM_OF_LEVELS - 1)
            while self.available_parking_lots_per_level[avail_shuttle_level] <= 0:
                avail_shuttle_level = random.randint(0, NUM_OF_LEVELS - 1)
            self.available_parking_lots_per_level[avail_shuttle_level] -= 1

        elif self.policy == "Balanced":
            # Lowest level first
            min_length = float("inf")
            avail_shuttle_level = 0
            for idx, s in enumerate(self.parking_lots_sets):
                if (
                    self.available_parking_lots_per_level[idx] > 0
                    and len(s) < min_length
                ):
                    avail_shuttle_level = idx
                    min_length = len(s)

            self.available_parking_lots_per_level[avail_shuttle_level] -= 1

            lengths = [len(s) for s in self.parking_lots_sets]
            length_strings = [str(length) for length in lengths]
            result = ", ".join(length_strings)
            print(result)

            print(self.available_parking_lots_per_level)

        # Request for shuttle
        self.check_shuttle_usage(avail_shuttle_level)
        shuttle = yield self.shuttles_stores[avail_shuttle_level].get()

        # Wait for available lift
        self.check_lift_usage(vehicle.id)
        lift = yield self.lifts_store.get()

        # Move Lift to ground level
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(dest=0)
        yield self.env.process(
            moveLift(
                self.env,
                self.layout,
                lift,
                0,
                lift_time_taken_to_ground,
                has_car=False,
                logger=self.logger,
            )
        )

        self.stats_box.stats["Cars Waiting"] -= 1

        # Driver Driving into the lift delay
        ground_lift_coord = findCoord(self.layout[1], lift)

        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        moveIntoGroundLift(vehicle, ground_lift_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)

        # Track time of service - START
        service_time_start = self.env.now

        self.logger.info(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (vehicle.id, lift.lift_num, self.env.now)
        )

        # Lift Travel Time to that level
        # TODO: Retrieving shuttle time while lift going up?
        # self.logger.info("LEVEL AVAILABLE: ", avail_shuttle_level)
        cur_level_layout = self.layout[avail_shuttle_level + 1]
        lift_coord = findCoord(cur_level_layout, lift)

        lift_time_taken = lift.time_taken_from_origin_to_dest(dest=avail_shuttle_level)
        yield self.env.process(
            moveLift(
                self.env,
                self.layout,
                lift,
                avail_shuttle_level,
                lift_time_taken,
                has_car=True,
                vehicle=vehicle,
                logger=self.logger,
            )
        )

        self.logger.info(
            "Car %d took lift %d and at level %d at %.2f"
            % (vehicle.id, lift.lift_num, avail_shuttle_level + 1, self.env.now)
        )

        # Shuttle from somewhere moves to lift position
        shuttle_time_taken = shuttle.time_taken_to_destination(lift.lift_num, lift=True)
        # Animate shuttle from current to next position
        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        moveShuttle(shuttle_sprite, shuttle_time_taken, lift_coord, lift=True)
        yield self.env.timeout(shuttle_time_taken)

        self.logger.info(
            "Level %d's shuttle %d is ready for loading at %.2f"
            % (avail_shuttle_level + 1, shuttle.shuttle_num, self.env.now)
        )

        # Policy 0: Finding the shortest available travel lot
        # Policy 1: Finding the random spot based on floor
        if self.policy == "Nearest-First" or self.policy == "Balanced":
            parking_lot_num = self.get_shortest_avail_travel_lot(
                lift, avail_shuttle_level
            )
        elif self.policy == "Randomised":
            parking_lot_num = self.random_parking_lot(lift, avail_shuttle_level)

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
        # self.logger.info("Parking: ", parking_coord)
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

        vehicle.popup.set_text("parked time", round(self.env.now, 2))
        self.logger.info(
            "Car %d parked at parking lot %d at %.2f"
            % (vehicle.id, parking_lot_num, self.env.now)
        )

        # Track time of service - END
        service_time_end = self.env.now
        self.stats_box.service_stats["parking"][vehicle.id] = round(
            service_time_end - service_time_start, 2
        )

        # Move shuttle back to default position and move back shuttle to default pos
        # TODO: Might have issues when waiting for shuttle to return to default pos
        self.env.process(
            self.moving_shuttle_back_to_default(
                shuttle, shuttle_sprite, avail_shuttle_level
            )
        )

        vehicle.parking_lot = (avail_shuttle_level, parking_lot_num)
        self.stats_box.stats["Cars Parked"] += 1

    def exit(self, vehicle, parking_lot_request):
        """
        Problem encountered: When shuttle is retrived and lift is full,
        car is unable to exit, resulting in a dead lock.
        Solution: Reserve a lift first and then shuttle?
        """
        self.logger.info(
            "Car %d is at level %d leaving the parking lot"
            % (vehicle.id, vehicle.parking_lot[0] + 1)
        )
        # Log waiting time - START
        time_start = self.env.now

        cur_level_layout = self.layout[vehicle.parking_lot[0] + 1]

        # Wait for available lift
        self.check_lift_usage(vehicle.id)
        # Get the closest lift
        lift_num, shuttle = yield self.env.process(
            self.get_shortest_to_lot_avail_lift(vehicle.parking_lot, cur_level_layout)
        )

        self.logger.info("Car %d reserving Lift %d" % (vehicle.id, lift_num))
        lift = yield self.lifts_store.get(lambda lift: lift.lift_num == lift_num)

        self.logger.info(
            "Car %d is at level %d reserved lift %d"
            % (vehicle.id, vehicle.parking_lot[0] + 1, lift_num)
        )

        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        parking_coord = findCoord(cur_level_layout, vehicle.parking_lot[1])

        # Shuttle from somewhere moves to parking_lot
        shuttle_time_taken = shuttle.time_taken_to_destination(vehicle.parking_lot[1])
        self.logger.info(
            "Car %d is at level %d using the shuttle"
            % (vehicle.id, vehicle.parking_lot[0] + 1)
        )
        # Animate shuttle from current to next position
        moveShuttle(shuttle_sprite, shuttle_time_taken, parking_coord)
        yield self.env.timeout(shuttle_time_taken)

        lift_coord = findCoord(cur_level_layout, lift)
        lift_coord_center = (lift_coord[0] + GRID_WIDTH, lift_coord[1])

        # Lift travel time to reach that level
        lift_time_taken = lift.time_taken_from_origin_to_dest(
            dest=vehicle.parking_lot[0]
        )
        yield self.env.process(
            moveLift(
                self.env,
                self.layout,
                lift,
                vehicle.parking_lot[0],
                lift_time_taken,
                has_car=False,
                logger=self.logger,
            )
        )

        # Travelling time from parking lot to lift - concurrent for lift travel time?
        time_taken_to_lift = lift.travel_times.get(vehicle.parking_lot[1])

        # Track time of service - START
        service_time_start = self.env.now

        movePalletToLot(vehicle, time_taken_to_lift["pallet_lot"], shuttle_sprite.pos)
        yield self.env.timeout(time_taken_to_lift["pallet_lot"])

        moveOriginToLot(
            vehicle, shuttle_sprite, time_taken_to_lift["pallet_lot"], lift_coord_center
        )
        yield self.env.timeout(time_taken_to_lift["pallet_lot"])

        moveLiftToPallet(vehicle, time_taken_to_lift["lift_pallet"], lift_coord_center)
        yield self.env.timeout(time_taken_to_lift["lift_pallet"])

        self.logger.info(
            "Car %d entered in lift bay and took lift %d at %.2f"
            % (vehicle.id, lift.lift_num, self.env.now)
        )

        # Lift travel time to reach ground level
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(dest=0)
        yield self.env.process(
            moveLift(
                self.env,
                self.layout,
                lift,
                0,
                lift_time_taken_to_ground,
                has_car=True,
                vehicle=vehicle,
                logger=self.logger,
            )
        )

        # Release parking spot
        self.available_parking_lots_per_level[vehicle.parking_lot[0]] += 1
        self.total_parking_lot_resources.release(parking_lot_request)
        self.parking_lots_sets[vehicle.parking_lot[0]].remove(vehicle.parking_lot[1])

        self.logger.info(
            "Car %d exited the carpark at %.2f" % (vehicle.id, self.env.now)
        )

        # Move shuttle back to default position and move back shuttle to default pos
        self.env.process(
            self.moving_shuttle_back_to_default(
                shuttle, shuttle_sprite, vehicle.parking_lot[0]
            )
        )
        vehicle.parking_lot = (None, None)
        self.stats_box.stats["Cars Parked"] -= 1
        self.stats_box.stats["Cars Exited"] += 1

        # Track time of service - END
        service_time_end = self.env.now
        self.stats_box.service_stats["retrieval"][vehicle.id] = round(
            service_time_end - service_time_start, 2
        )

        # Drove into the lift bay and driver drives out
        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        ground_floor_coord = findGroundLiftCoord(self.layout, lift)
        moveOutOfLift(vehicle, ground_floor_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)

        self.logger.info(
            "Car %d exits out of the carpark at %.2f" % (vehicle.id, self.env.now)
        )

        # Log waiting time - END
        time_end = self.env.now
        self.stats_box.waiting_stats["retrieval"][vehicle.id] = round(
            time_end - time_start, 2
        )

        # Put Lift back into store - lift will stay at whichever level it is at
        self.lifts_store.put(lift)

    def moving_shuttle_back_to_default(self, shuttle, shuttle_sprite, level):
        # Move shuttle back to default position
        time_taken = shuttle.move_to_default_pos()
        moveShuttle(shuttle_sprite, time_taken, shuttle_sprite.default_pos)
        yield self.env.timeout(time_taken)
        self.logger.info(
            "Level %d's Shuttle back to default position at %.2f"
            % (level + 1, self.env.now)
        )
        # Put shuttle back into store
        self.shuttles_stores[level].put(shuttle)
        self.shuttle_available_event.succeed()  # Trigger the event
        self.shuttle_available_event = self.env.event()
