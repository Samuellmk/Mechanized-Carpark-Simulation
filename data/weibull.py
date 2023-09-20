import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import weibull_min

# Define the shape parameter (k) and scale parameter (beta)
k = 1.359
lam = 3.68  # Increase this value to make the distribution wider
num_samples = 2000

# Generate random samples from the Weibull distribution
random_samples = weibull_min.rvs(c=k, scale=lam, size=num_samples)
print(list(random_samples))

# Define the x-axis range from 0 to 13 hours
x = np.linspace(0, 13, 1000)

# Calculate the Weibull PDF using the probability density function with the updated scale parameter
pdf = weibull_min.pdf(x, c=k, scale=lam)

# Set Seaborn style
sns.set(style="whitegrid")

# Create a single plot for both the histogram and the Weibull PDF using Matplotlib
plt.figure(figsize=(8, 6))

# Plot the histogram of the samples using Matplotlib's hist function
plt.hist(random_samples, bins=20, density=True, color="b", alpha=0.6, label="Histogram")

# Plot the Weibull PDF using Matplotlib's plot function
plt.plot(x, pdf, color="r", lw=2, label=f"Weibull PDF (k={k}, β={lam})")

plt.title(f"Weibull Distribution (k={k}, β={lam}) - Wider")
plt.xlabel("Hours")
plt.ylabel("Probability Density")
plt.legend()

plt.tight_layout()
plt.show()
