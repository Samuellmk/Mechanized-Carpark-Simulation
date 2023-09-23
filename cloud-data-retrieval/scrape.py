# import base64
# import functions_framework
import requests
from datetime import datetime, date
from google.cloud import storage
import os
import pytz

# Raffles City, Plaza Singapura, Vivocity P3, ION Orchard, Funan
# 1051, 695, 1388, 460, 390
CARPARK_MAX_LOTS = [905, 695, 1388, 460, 390]
CARPARKS_IDS = ["3", "9", "16", "23", "66"]

WEBSITE = "http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2"

# client = storage.Client()
client = storage.Client.from_service_account_json(
    "fyp-data-collection-399003-7ca5b40f442c.json"
)
bucket_name = "fyp-data-collection"
bucket = client.get_bucket(bucket_name)


def write_csv_to_storage(filename, data, headers):
    # Create or retrieve a blob in the bucket
    blob = bucket.blob(filename)

    if not blob.exists():
        # If the blob does not exist, write the headers first
        csv_data = ",".join(headers) + "\n" + ",".join(map(str, data.values())) + "\n"
    else:
        # If the blob exists, read the existing data and append the new data
        existing_data = blob.download_as_text()
        csv_data = (
            existing_data.strip() + "\n" + ",".join(map(str, data.values())) + "\n"
        )

    # Upload the data to the blob
    blob.upload_from_string(
        data=csv_data,
        content_type="text/csv",
    )


def get_carpark_occupancy():
    global bucket
    print("Fetching...")

    headers = {"AccountKey": os.getenv("KEY")}
    response = requests.get(WEBSITE, headers=headers)
    carpark_json = response.json()
    cp_data = carpark_json["value"]

    carpark = []

    current_utc_time = datetime.now(pytz.utc)
    singapore_timezone = pytz.timezone("Asia/Singapore")
    singapore_time = current_utc_time.astimezone(singapore_timezone)

    for data in cp_data:
        if data["CarParkID"] in CARPARKS_IDS:
            idx = CARPARKS_IDS.index(data["CarParkID"])

            cp_max_lot = CARPARK_MAX_LOTS[idx]

            remaining_lot = cp_max_lot - int(data["AvailableLots"])

            # Create a datetime object with the current time in UTC

            time_lot = singapore_time.strftime("%d-%m-%Y %H:%M:%S")

            carpark.append(
                {
                    "carparkID": data["CarParkID"],
                    "name": data["Development"],
                    "remainingLots": remaining_lot,
                    "timestamp": time_lot,
                }
            )

    field_names = list(carpark[0].keys())
    today = singapore_time.strftime("%Y-%m-%d")
    print(today)

    for mall in carpark:
        file_name = f"data/{mall['name']}-{today}.csv"
        print("Writing to %s..." % file_name)
        write_csv_to_storage(file_name, mall, field_names)


get_carpark_occupancy()

# # Triggered from a message on a Cloud Pub/Sub topic.
# @functions_framework.cloud_event
# def hello_pubsub(cloud_event):
#     # print out the data from Pub/Sub, to prove that it worked
#     print("Pub/sub msg:", base64.b64decode(cloud_event.data["message"]["data"]))
#     get_carpark_occupancy()
