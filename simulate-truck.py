# initialization module
NUMBER_TRUCK_SCALES = 1
NOT_ALLOWED_NUMBER = 4
TRUCK_ARRIVAL_MEAN = 3
TRUCK_SERVICE_MEAN = 3.0
TRUCK_SERVICE_STD = 0.5
SIM_TIME = 100
arrivals, departures = [], []
in_queue, in_system = [], []
tme_in_queue, len_in_queue = [], []


def truck_arrival(env, number_scales):
    # IDs for trucks
    next_truck_id = 0
    while True:
        ## exponential distribution for arrivals
        next_truck = expon.rvs(scale=TRUCK_ARRIVAL_MEAN, size=1)
        # Wait for the truck
        yield env.timeout(next_truck)
        time_of_arrival = env.now
        arrivals.append(time_of_arrival)
        next_truck_id += 1
        print("%3d arrives at %.2f" % (next_truck_id, env.now))

        env.process(wheighing(env, number_scales, next_truck_id, time_of_arrival))


def wheighing(env, number_scales, truck_number, time_of_arrival):
    with scales_lines.request() as req:
        print("%3d enters the queue at %.2f" % (truck_number, env.now))
        queue_in = env.now
        length = len(scales_lines.queue)
        tme_in_queue.append(queue_in)
        len_in_queue.append(length)
        yield req
        print("%3d leaves the queue at %.2f" % (truck_number, env.now))
        queue_out = env.now
        length = len(scales_lines.queue)
        tme_in_queue.append(queue_out)
        len_in_queue.append(length)
        # normal distribution for the weighing process
        r_normal = norm.rvs(loc=TRUCK_SERVICE_MEAN, scale=TRUCK_SERVICE_STD, size=1)
        yield env.timeout(r_normal)
        print("%3d permanece %.2f" % (truck_number, r_normal))
        time_of_departure = env.now
        departures.append(time_of_departure)
        time_in_system = time_of_departure - time_of_arrival
        in_system.append(time_in_system)
        time_in_queue = queue_out - queue_in
        in_queue.append(time_in_queue)


## set up the environment
env = simpy.Environment()
## defining resources
scales_lines = simpy.Resource(env, capacity=NUMBER_TRUCK_SCALES)
## selecting a random seed for the probability distributions
RANDOM_SEEDS = [1234, 5678, 9012, 3456, 7890]
np.random.seed(seed=RANDOM_SEEDS[1])
## defining the truck arrival process
env.process(truck_arrival(env, scales_lines))
## run the simultion
env.run(until=SIM_TIME)
