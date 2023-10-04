import random
import simpy
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
    def __init__(self, env, total_parking_lots, parking_lots_sets, lifts, shuttles, layout, stats_box, logger):
        self.env = env
        # To keep track the total amount of carpark lots available
        self.total_parking_lot_resources = total_parking_lots
        # A list of set, [<Set for level 1 cars>, ...], to keep track each level lots
        self.parking_lots_sets = parking_lots_sets
        self.available_parking_lots_per_level = [NUM_OF_PARKING_PER_LEVEL] * NUM_OF_LEVELS
        self.lifts_store = lifts
        self.shuttles_stores = shuttles
        self.time_taken = {}
        self.parking_queue = []
        self.layout = layout
        self.stats_box = stats_box
        self.policy = 0
        self.logger = logger
        self.status_tracker = None

    def update_status(self):
        while True:
            self.status_tracker.s_lifts = self.lifts_store
            self.status_tracker.s_shuttles = self.shuttles_stores

            yield self.env.timeout(5 / 60)  # Every 5s

    def get_shortest_avail_travel_lot(self, lift, level):
        available_lots = [lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]]
        # self.logger.info("Available lots:", available_lots)
        shortest_time_lot = min(available_lots, key=lambda lot: lift.travel_times[lot]["total"])
        # self.logger.info(shortest_time_lot)
        return shortest_time_lot

    def random_parking_lot(self, lift, level):
        available_lots = [lot for lot in lift.travel_times if lot not in self.parking_lots_sets[level]]
        random_parking = random.choice(available_lots)
        return random_parking

    def get_remaining_parking_lots(self):
        return self.total_parking_lot_resources.capacity - self.total_parking_lot_resources.count

    def get_parking_queue(self):
        return self.parking_queue

    def get_shortest_to_lot_avail_lift(self, parking_info):
        _, parking_num = parking_info

        while True:
            num = self.get_shortest_to_lot_lift(parking_num)

            if num is not None:
                break  # Exit the loop if num is not None
            yield self.env.timeout(1 / 60)
            # self.logger.info(f"Floor {floor_num + 1} Shuttle availability: {self.shuttles_stores[floor_num].items}")

            # available_lifts = [lift.num for lift in self.lifts_store.items]
            # sorted_lifts = sorted(available_lifts)
            # self.logger.info("Lifts %s are available at %.2f" % (", ".join(map(str, sorted_lifts)), self.env.now))

        # Request for shuttle
        # self.check_shuttle_usage(floor_num)
        # shuttle = yield self.shuttles_stores[floor_num].get()

        return num

    def get_shortest_to_lot_lift(self, parking_lot_num):
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
                min_lift = lift.num

        return min_lift

    def check_lift_usage(self, car_id):
        if len(self.lifts_store.items) == 0:
            self.logger.info("Car %d - Lifts are currently all occupied at %.2f" % (car_id, self.env.now))
        else:
            available_lifts = [lift.num for lift in self.lifts_store.items]
            sorted_lifts = sorted(available_lifts)
            self.logger.info("Lifts %s are available at %.2f" % (", ".join(map(str, sorted_lifts)), self.env.now))

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
            if len(shuttle_store.items) > 0 and self.available_parking_lots_per_level[idx] > 0:
                self.available_parking_lots_per_level[idx] -= 1
                return idx

    def get_shuttle_level_availability(self):
        # check if which level shuttle is free
        # Possible deadlock when car wants to come out but lift is full

        floor_level = None
        while floor_level == None:
            floor_level = self.check_shuttle_availability()
            yield self.env.timeout(1 / 60)

            if floor_level is not None:
                break

        # Request for shuttle
        # self.check_shuttle_usage(avail_shuttle_level)
        return floor_level

    def check_shuttle_usage(self, level):
        cur_shuttle = self.shuttles_stores[level].items
        if level == 1 and len(cur_shuttle) > 0:
            self.logger.warning("shuttle pos %d" % cur_shuttle[0].cur_pos)
        if len(cur_shuttle) == 0:
            self.logger.info("Level %d's Shuttle is currently all occupied at %.2f" % (level + 1, self.env.now))

    def move_lift_ground_level(self, lift, vehicle=None, release=False):
        lift_time_taken_to_ground = lift.time_taken_from_origin_to_dest(dest=0)
        yield self.env.process(
            moveLift(
                self.env,
                self.layout,
                lift,
                0,
                lift_time_taken_to_ground,
                vehicle=vehicle,
                logger=self.logger,
            )
        )
        if release:
            yield self.lifts_store.put(lift)

    def park(self, vehicle):
        # To which level? Check based on shuttle and available level

        if self.policy == "Nearest-First":
            avail_shuttle_level = yield self.env.process(self.get_shuttle_level_availability())  # index 0

        elif self.policy == "Randomised":
            avail_shuttle_level = random.randint(0, NUM_OF_LEVELS - 1)
            while self.available_parking_lots_per_level[avail_shuttle_level] <= 0:
                avail_shuttle_level = random.randint(0, NUM_OF_LEVELS - 1)
                yield self.env.timeout(1 / 60)
            self.available_parking_lots_per_level[avail_shuttle_level] -= 1

        elif self.policy == "Balanced":
            # Lowest level first
            min_length = float("inf")
            avail_shuttle_level = 0
            for idx, s in enumerate(self.parking_lots_sets):
                if self.available_parking_lots_per_level[idx] > 0 and len(s) < min_length:
                    avail_shuttle_level = idx
                    min_length = len(s)

            self.available_parking_lots_per_level[avail_shuttle_level] -= 1

        elif self.policy == "Cache":
            # Ground Level - Cache
            avail_shuttle_level = 0

            while self.available_parking_lots_per_level[avail_shuttle_level] <= 0:
                # Get the subsequent floor instead
                avail_shuttle_level = (avail_shuttle_level + 1) % NUM_OF_LEVELS
                yield self.env.timeout(1 / 60)

            self.available_parking_lots_per_level[avail_shuttle_level] -= 1

        else:
            raise Exception("No policy specified...")
        # Request for shuttle
        self.check_shuttle_usage(avail_shuttle_level)
        shuttle = yield self.shuttles_stores[avail_shuttle_level].get()

        # Wait for available lift
        self.check_lift_usage(vehicle.id)
        lift = yield self.lifts_store.get()

        # Move Lift to ground level
        yield self.env.process(self.move_lift_ground_level(lift))

        self.stats_box.stats["Cars Waiting"] -= 1

        # Driver Driving into the lift delay
        ground_lift_coord = findCoord(self.layout[1], lift)

        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        moveIntoGroundLift(vehicle, ground_lift_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)

        # Track time of service - START
        service_time_start = self.env.now

        self.logger.info(
            "[Parking] Car %d entered in lift bay and took lift %d at %.2f" % (vehicle.id, lift.num, self.env.now)
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
                vehicle=vehicle,
                logger=self.logger,
            )
        )

        self.logger.info(
            "[Parking] Car %d took lift %d and at level %d at %.2f"
            % (vehicle.id, lift.num, avail_shuttle_level + 1, self.env.now)
        )

        # Shuttle from somewhere moves to lift position
        shuttle_time_taken, destination = shuttle.time_taken_to_destination(lift.num, lift=True)
        # Animate shuttle from current to next position
        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        moveShuttle(shuttle_sprite, shuttle_time_taken, lift_coord, lift=True)
        yield self.env.timeout(shuttle_time_taken)
        shuttle.set_pos(destination)

        self.logger.info(
            "[Parking] Level %d's shuttle %d is ready for loading at %.2f"
            % (avail_shuttle_level + 1, shuttle.num, self.env.now)
        )

        # Policy 0: Finding the shortest available travel lot
        # Policy 1: Finding the random spot based on floor
        if self.policy == "Randomised":
            parking_lot_num = self.random_parking_lot(lift, avail_shuttle_level)
        else:
            parking_lot_num = self.get_shortest_avail_travel_lot(lift, avail_shuttle_level)

        # Parking is reserved for this car
        self.parking_lots_sets[avail_shuttle_level].add(parking_lot_num)

        # Travelling time from front of the lift to parking lot
        time_taken_to_parking = lift.travel_times.get(parking_lot_num)

        moveLiftToPallet(vehicle, time_taken_to_parking["lift_pallet"], shuttle_sprite.pos)
        yield self.env.timeout(time_taken_to_parking["lift_pallet"])

        # Put lift back into store - send lift back to ground level
        self.env.process(self.move_lift_ground_level(lift, release=True))

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
            "[Parking] Car %d parked at parking lot %d at %.2f" % (vehicle.id, parking_lot_num, self.env.now)
        )

        # Track time of service - END
        service_time_end = self.env.now
        self.stats_box.service_stats["parking"][vehicle.id] = round(service_time_end - service_time_start, 2)

        vehicle.parking_lot = (avail_shuttle_level, parking_lot_num)
        self.stats_box.stats["Cars Parked"] += 1

        # Move shuttle back to default position and move back shuttle to default pos
        # TODO: Might have issues when waiting for shuttle to return to default pos
        self.env.process(self.moving_shuttle_back_to_default(shuttle, shuttle_sprite, avail_shuttle_level))

    def exit(self, vehicle, parking_lot_request, lift=None, shuttle=None, state=0):
        """
        Problem encountered: When shuttle is retrived and lift is full,
        car is unable to exit, resulting in a dead lock.
        Solution: Reserve a lift first and then shuttle?
        """
        self.logger.info(
            "[Exiting] Car %d is at level %d leaving the parking lot" % (vehicle.id, vehicle.parking_lot[0] + 1)
        )
        # Log waiting time - START
        time_start = self.env.now

        cur_level_layout = self.layout[vehicle.parking_lot[0] + 1]

        if not lift and not shuttle:
            # Wait for available lift
            self.check_lift_usage(vehicle.id)
            # Get the closest lift
            num = yield self.env.process(self.get_shortest_to_lot_avail_lift(vehicle.parking_lot))
            shuttle = yield self.shuttles_stores[vehicle.parking_lot[0]].get()
            lift = yield self.lifts_store.get(lambda lift: lift.num == num)
            self.logger.info(
                "[Exiting] Car %d reserving lift %d and level %d shuttle" % (vehicle.id, num, vehicle.parking_lot[0])
            )
        else:
            self.logger.info(
                "[Exiting] Car %d is at level %d reserved lift %d and level %d shuttle"
                % (vehicle.id, vehicle.parking_lot[0] + 1, lift.num, vehicle.parking_lot[0])
            )

        shuttle_sprite = findShuttle(cur_level_layout, shuttle)
        parking_coord = findCoord(cur_level_layout, vehicle.parking_lot[1])

        if state < 6 or state == 9:
            # Shuttle from somewhere moves to parking_lot
            shuttle_time_taken, destination = shuttle.time_taken_to_destination(vehicle.parking_lot[1])
            self.logger.info(
                "[Exiting] Car %d is at level %d using the shuttle" % (vehicle.id, vehicle.parking_lot[0] + 1)
            )
            # Animate shuttle from current to next position
            moveShuttle(shuttle_sprite, shuttle_time_taken, parking_coord)
            yield self.env.timeout(shuttle_time_taken)
            shuttle.set_pos(destination)

        lift_coord = findCoord(cur_level_layout, lift)
        lift_coord_center = (lift_coord[0] + GRID_WIDTH, lift_coord[1])

        if state < 6 or state >= 8:
            # Lift travel time to reach that level
            lift_time_taken = lift.time_taken_from_origin_to_dest(dest=vehicle.parking_lot[0])
            yield self.env.process(
                moveLift(
                    self.env,
                    self.layout,
                    lift,
                    vehicle.parking_lot[0],
                    lift_time_taken,
                    logger=self.logger,
                )
            )

        # Travelling time from parking lot to lift - concurrent for lift travel time?
        time_taken_to_lift = lift.travel_times.get(vehicle.parking_lot[1])

        # Track time of service - START
        service_time_start = self.env.now

        if state < 4 or state >= 8:
            movePalletToLot(vehicle, time_taken_to_lift["pallet_lot"], shuttle_sprite.pos)
            yield self.env.timeout(time_taken_to_lift["pallet_lot"])
        if state < 6 or state >= 8:
            moveOriginToLot(vehicle, shuttle_sprite, time_taken_to_lift["pallet_lot"], lift_coord_center)
            yield self.env.timeout(time_taken_to_lift["pallet_lot"])

            moveLiftToPallet(vehicle, time_taken_to_lift["lift_pallet"], lift_coord_center)
            yield self.env.timeout(time_taken_to_lift["lift_pallet"])

            self.logger.info(
                "[Exiting] Car %d entered in lift bay and took lift %d at %.2f" % (vehicle.id, lift.num, self.env.now)
            )

        # Lift travel time to reach ground level
        # TODO: vehicle is not moving with the lift to exit
        yield self.env.process(self.move_lift_ground_level(lift, vehicle))
        self.logger.info("[Exiting] Lift %d move to level %d at %.2f" % (lift.num, lift.pos + 1, self.env.now))

        # Release parking spot
        self.available_parking_lots_per_level[vehicle.parking_lot[0]] += 1
        self.total_parking_lot_resources.release(parking_lot_request)
        self.parking_lots_sets[vehicle.parking_lot[0]].remove(vehicle.parking_lot[1])

        self.logger.info("[Exiting] Car %d exited the carpark at %.2f" % (vehicle.id, self.env.now))

        # Move shuttle back to default position and move back shuttle to default pos
        self.env.process(self.moving_shuttle_back_to_default(shuttle, shuttle_sprite, vehicle.parking_lot[0]))

        self.stats_box.stats["Cars Parked"] -= 1
        self.stats_box.stats["Cars Exited"] += 1

        # Track time of service - END
        service_time_end = self.env.now
        self.stats_box.service_stats["retrieval"][vehicle.id] = round(service_time_end - service_time_start, 2)

        # Drove into the lift bay and driver drives out
        drive_time_taken = random.uniform(*DRIVE_IN_OUT)
        ground_floor_coord = findGroundLiftCoord(self.layout, lift)
        moveOutOfLift(vehicle, ground_floor_coord, drive_time_taken)
        yield self.env.timeout(drive_time_taken)

        self.logger.info("[Exiting] Car %d exits out of the carpark at %.2f" % (vehicle.id, self.env.now))

        # Log waiting time - END
        time_end = self.env.now
        self.stats_box.waiting_stats["retrieval"][vehicle.id] = round(time_end - time_start, 2)

        vehicle.parking_lot = (None, None)

        # Put lift back into store
        yield self.lifts_store.put(lift)

    def move_vehicle_on_idle_shuttle(self, vehicle, parking_lot_request):
        state = 0
        shuttle, lift = None, None
        f_level, f_parking_lot_num, f_shuttle, f_shuttle_sprite = None, None, None, None
        lift_p = None
        time_taken_to_parking = None
        try:
            while True:
                # self.logger.warning(self.available_parking_lots_per_level)
                self.logger.warning("Car %d waiting to move to higher level" % (vehicle.id))

                for f_level, level_avail_lots in enumerate(self.available_parking_lots_per_level):
                    if f_level == 0:
                        continue
                    if (
                        level_avail_lots > 0
                        and self.parking_lots_sets[0]
                        and self.shuttles_stores[0].items
                        and self.lifts_store.items
                        and self.shuttles_stores[f_level].items
                    ):
                        # ----------GROUND FLOOR----------
                        # Interrupt in case the vehicle wants to exit during shuffling?
                        layout = self.layout[1]
                        # Get the closest lift and floor shuttle

                        self.logger.info("[Cache] Car %d is reserving shuttle" % (vehicle.id))
                        self.check_shuttle_usage(f_level)
                        f_shuttle = yield self.shuttles_stores[f_level].get()
                        num = yield self.env.process(self.get_shortest_to_lot_avail_lift(vehicle.parking_lot))
                        shuttle = yield self.shuttles_stores[vehicle.parking_lot[0]].get()
                        lift = yield self.lifts_store.get(lambda lift: lift.num == num)
                        self.logger.info(
                            "[Cache] Car %d reserving Lift %d and levels %d, %d shuttle at %.2f"
                            % (vehicle.id, num, 0, f_level, self.env.now)
                        )

                        print(lift, shuttle)

                        # Need to find a parking spot in higher level and reserve it
                        f_parking_lot_num = self.get_shortest_avail_travel_lot(lift, f_level)

                        self.available_parking_lots_per_level[f_level] -= 1
                        self.parking_lots_sets[f_level].add(f_parking_lot_num)

                        # Move Lift to ground level
                        yield self.env.process(self.move_lift_ground_level(lift))
                        state = 1

                        shuttle_sprite = findShuttle(layout, shuttle)
                        parking_coord = findCoord(layout, vehicle.parking_lot[1])

                        # Shuttle from somewhere moves to parking_lot
                        (
                            shuttle_time_taken,
                            destination,
                        ) = shuttle.time_taken_to_destination(vehicle.parking_lot[1])
                        self.logger.info("[Cache] Car %d is at level %d using the shuttle" % (vehicle.id, 1))
                        # Animate shuttle from current to next position
                        moveShuttle(shuttle_sprite, shuttle_time_taken, parking_coord)
                        yield self.env.timeout(shuttle_time_taken)
                        shuttle.set_pos(destination)
                        state = 2

                        lift_coord = findCoord(layout, lift)
                        lift_coord_center = (lift_coord[0] + GRID_WIDTH, lift_coord[1])

                        time_taken_to_lift = lift.travel_times.get(vehicle.parking_lot[1])

                        movePalletToLot(
                            vehicle,
                            time_taken_to_lift["pallet_lot"],
                            shuttle_sprite.pos,
                        )
                        yield self.env.timeout(time_taken_to_lift["pallet_lot"])
                        state = 3

                        moveOriginToLot(
                            vehicle,
                            shuttle_sprite,
                            time_taken_to_lift["pallet_lot"],
                            lift_coord_center,
                        )
                        yield self.env.timeout(time_taken_to_lift["pallet_lot"])
                        state = 4

                        moveLiftToPallet(
                            vehicle,
                            time_taken_to_lift["lift_pallet"],
                            lift_coord_center,
                        )
                        yield self.env.timeout(time_taken_to_lift["lift_pallet"])

                        self.logger.info(
                            "[Cache] Car %d entered in lift bay and took lift %d at %.2f"
                            % (vehicle.id, lift.num, self.env.now)
                        )
                        state = 5

                        self.env.process(self.moving_shuttle_back_to_default(shuttle, shuttle_sprite, 0))

                        # ----------GROUND FLOOR END----------

                        # Going up the lift to be parked
                        lift_time_taken_to_higher_level = lift.time_taken_from_origin_to_dest(dest=f_level)
                        lift_p = self.env.process(
                            moveLift(
                                self.env,
                                self.layout,
                                lift,
                                f_level,
                                lift_time_taken_to_higher_level,
                                vehicle=vehicle,
                                logger=self.logger,
                            )
                        )
                        yield lift_p

                        self.logger.info(
                            "[Cache] Car %d took lift %d and at level %d at %.2f"
                            % (
                                vehicle.id,
                                lift.num,
                                f_level + 1,
                                self.env.now,
                            )
                        )
                        state = 6

                        # ----------HIGHER FLOOR----------
                        f_layout = self.layout[f_level + 1]

                        # Shuttle from somewhere moves to lift position
                        (
                            shuttle_time_taken,
                            destination,
                        ) = f_shuttle.time_taken_to_destination(lift.num, lift=True)
                        # Animate shuttle from current to next position
                        f_shuttle_sprite = findShuttle(f_layout, f_shuttle)
                        moveShuttle(f_shuttle_sprite, shuttle_time_taken, lift_coord, lift=True)
                        yield self.env.timeout(shuttle_time_taken)
                        f_shuttle.set_pos(destination)
                        state = 7

                        # Travelling time from front of the lift to parking lot
                        time_taken_to_parking = lift.travel_times.get(f_parking_lot_num)

                        moveLiftToPallet(
                            vehicle,
                            time_taken_to_parking["lift_pallet"],
                            f_shuttle_sprite.pos,
                        )
                        yield self.env.timeout(time_taken_to_parking["lift_pallet"])
                        state = 8

                        # Put lift back into store - send lift back to ground level
                        self.env.process(self.move_lift_ground_level(lift, release=True))

                        parking_coord = findCoord(f_layout, f_parking_lot_num)

                        moveOriginToLot(
                            vehicle,
                            f_shuttle_sprite,
                            time_taken_to_parking["origin_lot"],
                            parking_coord,
                        )
                        yield self.env.timeout(time_taken_to_parking["origin_lot"])
                        state = 9

                        movePalletToLot(vehicle, time_taken_to_parking["pallet_lot"], parking_coord)
                        yield self.env.timeout(time_taken_to_parking["pallet_lot"])

                        # vehicle.popup.set_text("parked time", round(self.env.now, 2))
                        self.logger.info(
                            "[Cache] Car %d parked at level %d parking lot %d at %.2f"
                            % (vehicle.id, f_level, f_parking_lot_num, self.env.now)
                        )

                        self.env.process(self.moving_shuttle_back_to_default(f_shuttle, f_shuttle_sprite, f_level))
                        # ----------HIGHER FLOOR END----------

                        # Release parking spot from ground level
                        self.available_parking_lots_per_level[0] += 1
                        self.parking_lots_sets[0].remove(vehicle.parking_lot[1])

                        vehicle.parking_lot = (f_level, f_parking_lot_num)
                        return

                yield self.env.timeout(3 / 60)
        except simpy.Interrupt:
            self.logger.info("[Cache] Car %d is not going to be shifted, stopped at state %d" % (vehicle.id, state))
            self.logger.warning(f"{f_shuttle}")
        parking_coord = findCoord(self.layout[f_level + 1], f_parking_lot_num)

        if state >= 1:
            self.available_parking_lots_per_level[f_level] += 1
            self.parking_lots_sets[f_level].remove(f_parking_lot_num)

        if state == 5:
            lift_p.interrupt()

        elif state == 6:
            if f_shuttle == None:
                f_shuttle = yield self.shuttles_stores[f_level].get()
            f_shuttle_sprite = findShuttle(self.layout[f_level + 1], f_shuttle)
            moveShuttle(f_shuttle_sprite, shuttle_time_taken, lift_coord, lift=True)
            yield self.env.timeout(shuttle_time_taken)
            f_shuttle.set_pos(destination)
            yield self.env.process(self.moving_shuttle_back_to_default(f_shuttle, f_shuttle_sprite, f_level))

        elif state == 7:
            moveLiftToPallet(
                vehicle,
                time_taken_to_parking["lift_pallet"],
                f_shuttle_sprite.pos,
            )
            yield self.env.timeout(time_taken_to_parking["lift_pallet"])

            lift_time_taken_to_higher_level = lift.time_taken_from_origin_to_dest(dest=f_level)
            yield self.env.process(
                moveLift(
                    self.env,
                    self.layout,
                    lift,
                    f_level,
                    lift_time_taken_to_higher_level,
                    logger=self.logger,
                )
            )

            lift_coord = findCoord(self.layout[f_level + 1], lift)
            lift_coord_center = (lift_coord[0] + GRID_WIDTH, lift_coord[1])

            moveLiftToPallet(vehicle, time_taken_to_lift["lift_pallet"], lift_coord_center)
            yield self.env.timeout(time_taken_to_lift["lift_pallet"])

            self.logger.info(
                "[Exiting] Car %d entered in lift bay and took lift %d at %.2f" % (vehicle.id, lift.num, self.env.now)
            )

        elif state == 8:
            moveOriginToLot(
                vehicle,
                f_shuttle_sprite,
                time_taken_to_parking["origin_lot"],
                parking_coord,
            )
            yield self.env.timeout(time_taken_to_parking["origin_lot"])

        elif state == 9:
            movePalletToLot(vehicle, time_taken_to_parking["pallet_lot"], parking_coord)
            yield self.env.timeout(time_taken_to_parking["pallet_lot"])

        if state >= 8:
            self.available_parking_lots_per_level[0] += 1
            self.parking_lots_sets[0].remove(vehicle.parking_lot[1])

            self.available_parking_lots_per_level[f_level] -= 1
            self.parking_lots_sets[f_level].add(f_parking_lot_num)
            vehicle.parking_lot = (f_level, f_parking_lot_num)

            shuttle = f_shuttle  # so the correct level shuttle is selected

        yield self.env.process(self.exit(vehicle, parking_lot_request, lift, shuttle, state))

    def moving_shuttle_back_to_default(self, shuttle, shuttle_sprite, level):
        # Move shuttle back to default position
        time_taken, destination = shuttle.move_to_default_pos()
        moveShuttle(shuttle_sprite, time_taken, shuttle_sprite.default_pos)
        yield self.env.timeout(time_taken)
        shuttle.set_pos(destination)

        self.logger.info("Level %d's Shuttle back to default position at %.2f" % (level + 1, self.env.now))
        # Put shuttle back into store
        self.shuttles_stores[level].put(shuttle)
