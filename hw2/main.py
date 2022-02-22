import numpy as np
import numpy.random as rand
import pandas as pd

class Simulation():
    def __init__(self):
        self.arrival_times = [.81, .20, .49, .96, .90, .16, .27, .56, .84, .82, .99, .93, .02, .01, .13, .18, .20, .77, .43, .49, .90, .91, .62, .57]
        self.arrival_times = np.array(self.arrival_times)
        self.arrival_times = 50*self.arrival_times+5

        self.group_sizes = [.39, .27, .78, .90, .91, .49, .39, .88, .65, .37, .88, .87, .03, .09, .19, .83, .73, .43, .84,
                       .81, .07, .45, .67, .29]
        self.group_sizes = np.array(self.group_sizes)
        self.playing_times = np.zeros_like(self.group_sizes)
        for i in range(len(self.group_sizes)):
            if self.group_sizes[i] < .6:
                self.playing_times[i] = 60
            else:
                self.playing_times[i] = 120

        self.df_time_table = pd.DataFrame(columns=["Time", "Event"])
        self.C = 3
        self.arrival_times_counter = 0
        self.group_sizes_counter = 0

        self.event_I(0)


    def event_I(self,time):
        temp = {}
        temp["Time"] = time
        temp["Event"] = "I"
        self.df_time_table = self.df_time_table.append(temp, ignore_index=True)

        self.N = 0
        t_a = self.arrival_times[self.arrival_times_counter]
        self.arrival_times_counter = self.arrival_times_counter + 1
        self.event_A(time + t_a)

    def event_A(self,time):
        temp = {}
        temp["Time"] = time
        temp["Event"] = "A"
        self.df_time_table = self.df_time_table.append(temp, ignore_index=True)
        self.N = self.N + 1

        # CHECK FOR END POINT
        if self.arrival_times_counter == 24:
            return
        t_a = self.arrival_times[self.arrival_times_counter]
        self.arrival_times_counter = self.arrival_times_counter + 1
        self.event_A(time + t_a)
        if self.N < self.C:
            self.event_B(time)


    def event_B(self,time):
        temp = {}
        temp["Time"] = time
        temp["Event"] = "B"
        self.df_time_table = self.df_time_table.append(temp, ignore_index=True)

        if self.N < self.C:
            group_size = self.group_sizes[self.group_sizes_counter]
            self.group_size_counter = self.group_size_counter + 1
            if group_size < .6:
                t_s = 60
            else:
                t_s = 120
            self.event_E(time + t_s)


    def event_E(self,time):
        temp = {}
        temp["Time"] = time
        temp["Event"] = "E"
        self.df_time_table = self.df_time_table.append(temp, ignore_index=True)
        self.N = self.N - 1
        if self.N >= 3:
            self.event_B(time)

if __name__ == "__main__":
    s = Simulation()
    print(s.df_time_table)
