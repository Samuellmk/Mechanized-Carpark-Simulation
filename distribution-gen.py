import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, poisson

# Define the parameters for the morning and evening peaks
morning_mean = 8  # 8:00 AM
morning_std = 0.25  # Standard deviation for the morning peak arrivals (in hours)
evening_mean = 18  # 6:00 PM
evening_std = 0.25  # Standard deviation for the evening peak arrivals (in hours)

# Define the lambda parameter for the Poisson distribution during non-peak hours
non_peak_lambda = 5  # Average number of cars during non-peak hours

# Define the time range (24 hours)
hours = np.arange(24)

# Generate the probability density function (PDF) for each hour
pdf = np.zeros(24)
pdf += norm.pdf(hours, morning_mean, morning_std)  # Morning peak
pdf += norm.pdf(hours, evening_mean, evening_std)  # Evening peak
pdf /= np.sum(pdf)  # Normalize the PDF

# Generate random samples according to the PDF
num_samples = 1000
samples = np.random.choice(hours, size=num_samples, p=pdf)

# Replace samples within the morning and evening peaks with 0
samples[(samples >= 8) & (samples < 18)] = 0

# Generate the probability density function (PDF) for each hour
pdf = np.zeros(24)
pdf += norm.pdf(hours, morning_mean, morning_std)  # Morning peak
pdf += norm.pdf(hours, evening_mean, evening_std)  # Evening peak
pdf += np.full(24, non_peak_lambda)  # Non-peak hours
pdf /= np.sum(pdf)  # Normalize the PDF

# Generate random samples according to the PDF
num_samples = 1000
samples = np.random.choice(hours, size=num_samples, p=pdf)

# Plot the histogram of the generated samples
plt.hist(samples, bins=24, range=(0, 24), density=True, alpha=0.7)

# Plot the PDFs of the Gaussian distributions for the morning and evening peaks
x = np.linspace(0, 24, 1000)
morning_pdf = norm.pdf(x, morning_mean, morning_std)
evening_pdf = norm.pdf(x, evening_mean, evening_std)
plt.plot(x, morning_pdf, "r-", label="Morning Peak")
plt.plot(x, evening_pdf, "g-", label="Evening Peak")

# Calculate the PMF of the Poisson distribution during non-peak hours
non_peak_x = np.arange(np.max(samples) + 1)
non_peak_pmf = poisson.pmf(non_peak_x, non_peak_lambda)
plt.plot(non_peak_x, non_peak_pmf, "b-", label="Non-Peak Hours")

plt.xlabel("Time (hours)")
plt.ylabel("Probability Density")
plt.title("Car Arrivals in Residential Area")
plt.legend()
plt.show()
