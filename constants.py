# https://www.ura.gov.sg/Corporate/Guidelines/Circulars/dc11-04
WIDTH_PER_CAR = 2.4
LENGTH_PER_CAR = 5.4
HEIGHT_PER_CAR = 1.55
HEIGHT_PER_LEVEL = 2.2 + 0.3  # Allowance of ceiling lights
NUM_OF_LEVELS = 4  # 5
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
DRIVE_IN_OUT = (
    1 / 6,
    0.51,
)  # 10-30 seconds for driver to start/stop engine and get out
RETRIEVAL_TIME = 60

RANDOM_SEEDS = 12345
CAR_ARRIVAL_RATE = 0.25  # 2  # rate/min
MAX_CAR = 160

DEFAULT_LIFT_STATE = 0  # index start from 0

# coordinate
LIFTS = [9, 12, 15, 18]

# animation
WIDTH, HEIGHT = 1000, 800
GRID_WIDTH, GRID_HEIGHT = 32, 48
TOTAL_WIDTH = 26 * GRID_WIDTH + 4  # Border
STATS_HEIGHT = 26

FACTOR = 0.9  # 64x fast foward
# FACTOR = 1.875  # 32x fast foward
# FACTOR = 7.5
FPS = 60
TOLERANCE = 60 // FACTOR * 1.1

# TODO: shuttle are being "deadlock"
