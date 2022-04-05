import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList
from numpy.random import default_rng


class Simulation():
    def __init__(self,max_time=2000,rng_seed=None,arrival_rate=9,mean_parked_time=1,
                 max_parking_spaces=10,increased_arrival_rate=None):

        # Random number generator
        self.rng_generator = default_rng(rng_seed)

        self.df_time_table = pd.DataFrame(columns=["time",
                                                   "event",
                                                   "num_current_parked",
                                                   "num_total_arrivals",
                                                   "num_total_balks"])
        self.time_events_list = LinkedList()
        self.arrival_rate = arrival_rate
        self.mean_parked_time = mean_parked_time
        self.max_parking_spaces = max_parking_spaces
        self.increased_arrival_rate = increased_arrival_rate

        self.num_current_parked = None
        self.num_total_arrivals = None
        self.num_total_balks = None
        self.get_distr_parked = None

        # self.arrival_times = []
        # self.group_2_waittime = []
        # self.group_4_waittime = []
        
        self.event_list_empty = False
        self.max_time = max_time

        self.run()


    def event_I(self,curr_event):
        time = curr_event["time"]

        # Action
        self.num_current_parked = 0
        self.num_total_arrivals = 0
        self.num_total_balks = 0
        # Queue A
        t_a = self.rng_generator.exponential(1 / self.arrival_rate)
        temp = {}
        temp["time"] = time + t_a
        temp["event"] = "A"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        curr_event["num_current_parked"] = self.num_current_parked
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_total_balks"] = self.num_total_balks
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def event_A(self,curr_event):
        time = curr_event["time"]

        # Action
        self.num_total_arrivals += 1
        # See if car balks
        if self.num_current_parked == self.max_parking_spaces:
            self.num_total_balks += 1
        else:
            self.num_current_parked += 1
            temp = {}
            t_l = self.rng_generator.exponential(self.mean_parked_time)
            temp["time"] = time + t_l
            temp["event"] = "L"
            self.time_events_list.addNode(temp["time"], temp)
        # Queue up another A
        if self.increased_arrival_rate is None:
            t_a = self.rng_generator.exponential(1 / self.arrival_rate)
        else:
            time_of_day = time % 24
            if time_of_day > 4 and time_of_day < 6:
                t_a = self.rng_generator.exponential(1 / self.increased_arrival_rate)
            else:
                t_a = self.rng_generator.exponential(1 / self.arrival_rate)
        if time + t_a <= self.max_time:
            temp = {}
            temp["time"] = time + t_a
            temp["event"] = "A"
            self.time_events_list.addNode(temp["time"], temp)

        # Log
        curr_event["num_current_parked"] = self.num_current_parked
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_total_balks"] = self.num_total_balks
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def event_L(self,curr_event):
        time = curr_event["time"]

        # Action
        self.num_current_parked -= 1

        # Log
        curr_event["num_current_parked"] = self.num_current_parked
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_total_balks"] = self.num_total_balks
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def update(self):
        # Get next event
        temp = self.time_events_list.head.data
        if temp["event"] == "A":
            self.event_A(temp)
        elif temp["event"] == "B":
            self.event_B(temp)
        elif temp["event"] == "L":
            self.event_L(temp)
        elif temp["event"] == "I":
            self.event_I(temp)

        # Move head to next time
        self.time_events_list.head = self.time_events_list.head.next
        if self.time_events_list.head is None:
            self.event_list_empty = True

    def run(self):
        temp = {}
        temp["time"] = 0
        temp["event"] = "I"
        self.time_events_list.addNode(temp["time"],temp)

        while not self.event_list_empty:
            self.update()

    def get_fraction_cars_balked(self):
        return self.num_total_balks / self.num_total_arrivals

    def get_distr_num_current_parked(self):
        if self.get_distr_parked is None:
            self.df_distr = pd.DataFrame()
            self.df_distr['values'] = self.df_time_table["num_current_parked"][:-1]
            self.df_distr["weights"] = self.df_time_table["time"].diff()[1:].reset_index(drop=True)
            self.df_distr = self.df_distr.groupby("values").weights.sum()
            self.df_distr = self.df_distr / self.df_distr.sum()
            self.df_distr = self.df_distr.rename("Probabilities")
        return self.df_distr

    def get_avg_num_current_parked(self):
        df_distr = self.get_distr_num_current_parked()
        return np.dot(df_distr.index,df_distr)

if __name__ == "__main__":
    # Notes (Written for ST's clarity, saved in case XP was confused too)
    # - time is in hours. Including the expected time for a car to be parked.
    # - We use exponential rate for the next car since that models the time until the next
    #   poisson event
    # - Numpy takes the average as the input for the exponential function. The average of
    #   the exponential is 1/(the poisson rate)

    # todo XP
    # - Double check for phantom cars/spaces
    # - Double check wording that "looking over sets of 24 periods" means a continuous simulation
    #   and not running multiple sims for only 24 hours

    total_run_time = 500 # in hours
    seed = 53243

    s = Simulation(total_run_time,rng_seed=seed)
    print("With Normal Arrival Rate")
    print("------------------------")
    print(f"a) {s.get_fraction_cars_balked():.3f}")
    print(f"b) {s.get_distr_num_current_parked()}")
    print(f"c) {s.get_avg_num_current_parked():.3f}")
    print(s.get_distr_num_current_parked())
    print(s.get_avg_num_current_parked())

    s = Simulation(total_run_time,rng_seed=seed,increased_arrival_rate=12)
    print("\n With Increased Arrival Rate")
    print("---------------------------")
    print(f"a) {s.get_fraction_cars_balked():.3f}")
    print(f"b) {s.get_distr_num_current_parked()}")
    print(f"c) {s.get_avg_num_current_parked():.3f}")