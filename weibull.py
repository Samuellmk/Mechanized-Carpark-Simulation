import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

# Define the shape parameter (k) and scale parameter (beta)
k = 1.359
beta = 2.0  # Increase this value to make the distribution wider

# Generate random samples from the Weibull distribution
num_samples = 1000
random_samples = weibull_min.rvs(c=k, scale=beta, size=num_samples)

# Define the x-axis range from 0 to 13 hours
x = np.linspace(0, 13, 1000)

# Calculate the Weibull PDF using the probability density function with the updated scale parameter
pdf = weibull_min.pdf(x, c=k, scale=beta)

# Create a single plot for both the histogram and the Weibull PDF
plt.figure(figsize=(8, 6))

# Plot the histogram of the samples
plt.hist(random_samples, bins=20, density=True, alpha=0.6, color='b', label='Histogram')
plt.plot(x, pdf, 'r-', lw=2, label=f'Weibull PDF (k={k}, β={beta})')

plt.title(f'Weibull Distribution (k={k}, β={beta}) - Wider')
plt.xlabel('Hours')
plt.ylabel('Probability Density')
plt.legend()

plt.tight_layout()
plt.show()
