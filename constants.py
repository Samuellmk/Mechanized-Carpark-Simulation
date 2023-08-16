# https://www.ura.gov.sg/Corporate/Guidelines/Circulars/dc11-04
WIDTH_PER_CAR = 2.4
LENGTH_PER_CAR = 5.4
HEIGHT_PER_CAR = 1.55
HEIGHT_PER_LEVEL = 2.2 + 0.3  # Allowance of ceiling lights
NUM_OF_LEVELS = 2  # 5
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
RETRIEVAL_TIME = 0.01

RANDOM_SEEDS = 12345
CAR_ARRIVAL_RATE = 2  # rate/min
CAR_NUMBER = 10

# coordinate
LIFTS = [9, 12, 15, 18]
