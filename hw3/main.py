import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList


class Simulation():
    def __init__(self):

        # RNG for the arrival times
        self.arrival_times = [.81, .20, .49, .96, .90, .16, .27, .56, .84, .82, .99, .93, .02, .01, .13, .18, .20, .77, .43, .49, .90, .91, .62, .57]
        self.arrival_times = np.array(self.arrival_times)
        self.arrival_times = 50*self.arrival_times+5

        # RNG for the group sizes
        self.group_sizes = [.39, .27, .78, .90, .91, .49, .39, .88, .65, .37, .88, .87, .03, .09, .19, .83, .73, .43, .84,
                       .81, .07, .45, .67, .29]
        self.group_sizes = np.array(self.group_sizes)
        # self.playing_times = np.zeros_like(self.group_sizes)
        # for i in range(len(self.group_sizes)):
        #     if self.group_sizes[i] < .6:
        #         self.playing_times[i] = 60
        #     else:
        #         self.playing_times[i] = 120

        self.df_time_table = pd.DataFrame(columns=["Time", "Event","N","T_s","T_a"])
        self.time_events_list = LinkedList()
        self.C = 3
        self.arrival_times_counter = 0
        self.group_sizes_counter = 0
        self.rng_generator_full = False

        self.run()


    def event_I(self,curr_event):
        time  = curr_event["Time"]

        # Action
        self.N = 0

        # RNG
        t_a = self.arrival_times[self.arrival_times_counter]
        self.arrival_times_counter = self.arrival_times_counter + 1

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

        # RNG
        if self.arrival_times_counter == 24:
            self.rng_generator_full = True
            return
        t_a = self.arrival_times[self.arrival_times_counter]
        self.arrival_times_counter = self.arrival_times_counter + 1

        # Queue up more
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
        if self.group_sizes_counter == 24:
            self.rng_generator_full = True
            raise RuntimeError("This should not occur with the current RNG values")
            return
        group_size = self.group_sizes[self.group_sizes_counter]
        self.group_sizes_counter = self.group_sizes_counter + 1
        if group_size < .6:
            t_s = 60
        else:
            t_s = 120

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
            print(self.time_events_list.head)

    def run(self):
        temp = {}
        temp["Time"] = 0
        temp["Event"] = "I"
        self.time_events_list.addNode(temp["Time"],temp)

        while not self.rng_generator_full:
            self.update()


if __name__ == "__main__":
    s = Simulation()
    print(s.df_time_table)
