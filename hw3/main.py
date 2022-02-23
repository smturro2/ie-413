import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList
from numpy.random import default_rng


class Simulation():
    def __init__(self,max_time=2000,rng_seed=None):

        # Random number generator
        self.rng_generator = default_rng(rng_seed)

        self.df_time_table = pd.DataFrame(columns=["Time", "Event","N","T_s","T_a"])
        self.time_events_list = LinkedList()
        self.C = 3
        self.group_2_counter = 0
        self.group_4_counter = 0        
        
        self.arrival_times = []
        self.group_2_waittime = []
        self.group_4_waittime = []
        
        self.event_list_empty = False
        self.max_time = max_time

        self.run()


    def event_I(self,curr_event):
        time = curr_event["Time"]

        # Action
        self.N = 0

        # RNG
        t_a = self.rng_generator.uniform(5,55)

        # Queue up more
        temp = {}
        temp["Time"] = time + t_a
        temp["Event"] = "A"
        self.time_events_list.addNode(temp["Time"], temp)

        # Log
        curr_event["T_a"] = t_a
        curr_event["N"] = self.N
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def event_A(self,curr_event):
        time  = curr_event["Time"]

        # Action
        self.N = self.N + 1
        self.arrival_times.append(time)
        
        # RNG
        t_a = self.rng_generator.uniform(5,55)

        # Queue up more
        if time + t_a <= self.max_time:
            temp = {}
            temp["Time"] = time + t_a
            temp["Event"] = "A"
            self.time_events_list.addNode(temp["Time"], temp)

        if self.N <= self.C:
            temp = {}
            temp["Time"] = time
            temp["Event"] = "B"
            self.time_events_list.addNode(temp["Time"], temp)

        # Log
        curr_event["N"] = self.N
        curr_event["T_a"] = t_a
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)


    def event_B(self,curr_event):
        time  = curr_event["Time"]

        # RNG
        group_size = self.rng_generator.uniform()
        if group_size < .6:
            self.group_2_counter += 1
            t_s = 60
            self.group_2_waittime.append(time - self.arrival_times[0] + t_s)
            del self.arrival_times[0]
        else:
            self.group_4_counter += 1
            t_s = 120
            self.group_4_waittime.append(time - self.arrival_times[0] + t_s)
            del self.arrival_times[0]

        # Queue up more
        temp = {}
        temp["Time"] = time + t_s
        temp["Event"] = "E"
        self.time_events_list.addNode(temp["Time"], temp)

        # Log
        curr_event["T_s"] = t_s
        curr_event["N"] = self.N
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def event_E(self,curr_event):
        time  = curr_event["Time"]

        # Action
        self.N = self.N - 1

        # Queue up more
        if self.N >= 3:
            temp = {}
            temp["Time"] = time
            temp["Event"] = "B"
            self.time_events_list.addNode(temp["Time"], temp)

        # Log
        curr_event["N"] = self.N
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def update(self):
        # Get next event
        temp = self.time_events_list.head.data
        if temp["Event"] == "A":
            self.event_A(temp)
        elif temp["Event"] == "B":
            self.event_B(temp)
        elif temp["Event"] == "E":
            self.event_E(temp)
        elif temp["Event"] == "I":
            self.event_I(temp)

        # Move head to next time
        self.time_events_list.head = self.time_events_list.head.next
        if self.time_events_list.head is None:
            self.event_list_empty = True

    def run(self):
        temp = {}
        temp["Time"] = 0
        temp["Event"] = "I"
        self.time_events_list.addNode(temp["Time"],temp)

        while not self.event_list_empty:
            self.update()


if __name__ == "__main__":
    month = 43200 # minutes
    s = Simulation(month)
    print(s.df_time_table)
    final_time = s.df_time_table.iloc[len(s.df_time_table)-1]["Time"]
    num_group_2 = s.group_2_counter
    num_group_4 = s.group_4_counter
    
    days = final_time / 60 / 24
    
    # Part A
    print("Avg number of group size 2 per day:", num_group_2 / days)
    print("Avg number of group size 4 per day:", num_group_4 / days)
    print("Avg number of groups (combined) per day:", (num_group_2 + num_group_4) / days)
    
    # Part B
    group_2_waittime = s.group_2_waittime
    group_4_waittime = s.group_4_waittime
    mean_group_2 = np.mean(group_2_waittime)
    mean_group_4 = np.mean(group_4_waittime)
    mean_combined = np.mean(group_2_waittime.extend(group_4_waittime))
    
    print("Group 2 mean time in system:", mean_group_2, "minutes.")
    print("Group 4 mean time in system:", mean_group_4, "minutes.")
    print("Combined groups mean time in system:", mean_combined, "minutes.")



    