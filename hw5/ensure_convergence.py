import numpy as np
import matplotlib.pyplot as plt
from main import Simulation


if __name__ == "__main__":
    simulation_seed = 53243
    simulation_times = np.linspace(10,500,20)
    sim_count = 0


    avg_cars_parked_norm = list()
    frac_balked_norm = list()
    for total_run_time in simulation_times:
        s = Simulation(total_run_time,rng_seed=simulation_seed)

        avg_cars_parked_norm.append(s.get_avg_num_current_parked())
        frac_balked_norm.append(s.get_fraction_cars_balked())
        print(f"Simulation {sim_count+1}/{len(simulation_times)*2} Done.")
        sim_count += 1

    avg_cars_parked_inhomo = list()
    frac_balked_inhomo = list()
    for total_run_time in simulation_times:
        s = Simulation(total_run_time,rng_seed=simulation_seed,increased_arrival_rate=12)

        avg_cars_parked_inhomo.append(s.get_avg_num_current_parked())
        frac_balked_inhomo.append(s.get_fraction_cars_balked())
        print(f"Simulation {sim_count+1}/{len(simulation_times)*2} Done.")
        sim_count += 1


    plt.subplot(1,2,1)
    plt.plot(simulation_times,avg_cars_parked_norm,label="Normal Arrival Rate")
    plt.plot(simulation_times,avg_cars_parked_inhomo,label="InHomo Arrival Rate")
    plt.legend()
    plt.xlabel("Simulation Time")
    plt.ylabel("avg_cars_parked")

    plt.subplot(1,2,2)
    plt.plot(simulation_times,frac_balked_norm,label="Normal Arrival Rate")
    plt.plot(simulation_times,frac_balked_inhomo,label="InHomo Arrival Rate")
    plt.legend()
    plt.xlabel("Simulation Time")
    plt.ylabel("frac_balked")
    plt.tight_layout()
    plt.show()