import simpy
import sys

sys.path.append("F:\\NTU\\FYP\\Simulation\\classes")
from classes.lift import Lift
from classes.lobby import Lobby
from classes.shuttle import Shuttle
from constants import *
from classes.carpark import Carpark
from simulation.utils import create_lifts_data


def sim_init(env, carpark_layout, stats_box, logger, isCache=False):
    # Create Lobby Store
    lobby_store, lobby_travel_data = None, None
    total_parking_lots = simpy.Resource(env, NUM_OF_PARKING_PER_LEVEL * NUM_OF_LEVELS)
    if isCache:
        lobby_store = simpy.Store(env, capacity=1)
        lobby_travel_data = create_lifts_data(LOBBY, cache=True)[0]
        lobby_store.items.append(Lobby(env, 1, lobby_travel_data))
        total_parking_lots = simpy.Resource(
            env, NUM_OF_PARKING_PER_LEVEL * NUM_OF_LEVELS - 3
        )

    # Create Lifts Store
    lifts_travel_data = create_lifts_data(LIFTS, cache=False)

    lifts_store = simpy.FilterStore(env, capacity=NUM_OF_LIFTS)
    for i in range(1, NUM_OF_LIFTS + 1):
        lifts_store.items.append(
            Lift(
                env,
                i,
                lifts_travel_data[i - 1],
                DEFAULT_LIFT_STATE,
                lobby_travel_data,
            )
        )

    parking_lots_sets = []
    shuttles_stores = []
    for _ in range(NUM_OF_LEVELS):
        # Create Shuttle Store
        shuttles_store = simpy.Store(env, capacity=NUM_OF_SHUTTLE_PER_LEVEL)
        for i in range(1, NUM_OF_SHUTTLE_PER_LEVEL + 1):
            shuttles_store.items.append(Shuttle(env, i))
        shuttles_stores.append(shuttles_store)

        # Create Parking lot resources
        parking_lots_sets.append(set())

    carpark = Carpark(
        env,
        total_parking_lots,
        parking_lots_sets,
        lifts_store,
        shuttles_stores,
        carpark_layout,
        stats_box,
        logger,
        lobby_store,
        isCache=isCache,
    )

    return carpark
