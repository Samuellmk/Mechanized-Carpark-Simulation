import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd


def plot_waiting_time_retrieval(waiting_times):
    # Extract data from the waiting_times dictionary
    labels = list(waiting_times.keys())
    times = list(waiting_times.values())

    mean_waiting_time = np.mean(times)
    print("mean of waiting_time for car retrieval: %.2f" % mean_waiting_time)

    # Plot the data as a bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(labels, times, color="green")
    plt.xlabel("Car ID")
    plt.ylabel("Waiting Time for Retrieval")
    plt.title("Waiting Time for Retrieval of Cars")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Show the plot
    plt.show()
