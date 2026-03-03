import numpy as np
import matplotlib.pyplot as plt
from main import simulate

# temperature sweep
temps = np.linspace(-5, 20, 15)  # from -5°C to 20°C
runs = 2000  # simulations per temperature

survival_no_override = []
survival_override = []

for temp in temps:
    results_no = [simulate(temp_c=temp, override=False, steps=40) for _ in range(runs)]
    results_yes = [simulate(temp_c=temp, override=True, steps=40) for _ in range(runs)]

    survival_no_override.append(sum(results_no) / runs)
    survival_override.append(sum(results_yes) / runs)

# plot
plt.figure()
plt.plot(temps, survival_no_override, label='No Override')
plt.plot(temps, survival_override, label='Override')
plt.legend()

plt.xlabel('Temperature (°C)')
plt.ylabel('Survival Probability')
plt.title('Shuttle Survival vs Temperature')
plt.ylim(0, 1)

plt.show()