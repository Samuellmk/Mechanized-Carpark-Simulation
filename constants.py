# https://www.ura.gov.sg/Corporate/Guidelines/Circulars/dc11-04
WIDTH_PER_CAR = 2.4
LENGTH_PER_CAR = 5.4
HEIGHT_PER_CAR = 1.55
HEIGHT_PER_LEVEL = 2.2 + 0.3  # Allowance of ceiling lights
NUM_OF_LEVELS = 5
TOTAL_NUM_OF_PARKING = 195
NUM_OF_PARKING_PER_LEVEL = 39
NUM_OF_LIFTS = 4
NUM_OF_SHUTTLE_PER_LEVEL = 1
# SHUTTLE_ACC no data
SHUTTLE_SPEED = 90  # m/min
PALLET_SPEED = 45  # m/min
ROTARY = 3.5  # rpm
# LIFT_ACC no data
LIFT_SPEED = 65  # m/min

# All the distribution stats for
DRIVE_IN_OUT = (
    1 / 6,
    0.5,
)  # 10-30 seconds for driver to start/stop engine and get out
CAR_DURATION_SHAPE = 4.5
CAR_DURATION_SCALE = 1.5
CAR_RATE = 1 / 120

RANDOM_SEEDS = 12345

DEFAULT_LIFT_STATE = 0  # index start from 0

DATA_COLLECTION_INTERVAL = 5  # mins

# coordinate
LIFTS = [9, 12, 15, 18]

# animation
WIDTH, HEIGHT = 1000, 900
GRID_WIDTH, GRID_HEIGHT = 32, 48
TOTAL_WIDTH = 26 * GRID_WIDTH + 4  # Border
STATS_HEIGHT = 32 * 2
LIFT_IN_OUT_PX = 50

FACTOR = 0.23  # ~ 256x fast forward
# FACTOR = 0.47  # ~128x fast forward
# FACTOR = 0.9  # ~64x fast forward
# FACTOR = 1.875  # 32x fast forward
# FACTOR = 3.75  # 16x fast forward
# FACTOR = 7.5
FPS = 60
TOLERANCE = 60 // FACTOR * 1.2

ACTUAL_START_TIME = 0.0
