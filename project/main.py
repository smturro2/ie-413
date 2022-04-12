import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList
from numpy.random import default_rng

# Done: changed simulation
# Changed the log to reflect new columns
# To do: add event P, which processes all existing customers at the start of the day
# Loop event P and ensure it's working correctly


class Simulation():
    # def __init__(self,max_time=2000,rng_seed=None,arrival_rate=9,mean_parked_time=1,
    #            max_parking_spaces=10,increased_arrival_rate=None):

    def __init__(self, max_time = 2000, rng_seed = None,
               checkin_rate = 12, roadtest_rate = 2, camera_rate = 2, 
               clerk_rate = 1, writtentest_rate = 0.5, cashier_rate = 3,
               arrival_rate = 9, increased_arrival_rate = 25,
               allocation_policy = None):
              
              
              
        # Random number generator
        self.rng_generator = default_rng(rng_seed)

        # self.df_time_table = pd.DataFrame(columns=["time",
        #                                            "event",
        #                                            "num_current_parked",
        #                                            "num_total_arrivals",
        #                                            "num_total_balks"])
        
        self.df_time_table = pd.DataFrame(columns=["time",
                                                   "event",
                                                   "num_total_arrivals",
                                                   "num_line_checkin_inside",
                                                   "num_line_checkin_outside",
                                                   "num_line_camera",
                                                   "num_line_clerk",
                                                   "num_line_roadtest",
                                                   "num_line_writtentest",
                                                   "num_line_cashier"])
        
        self.time_events_list = LinkedList()
        self.checkin_rate = checkin_rate
        self.roadtest_rate = roadtest_rate
        self.camera_rate = camera_rate
        self.clerk_rate = clerk_rate
        self.writtentest_rate = writtentest_rate
        self.cashier_rate = cashier_rate
        self.arrival_rate = arrival_rate
        self.increased_arrival_rate = increased_arrival_rate
        
        self.num_total_arrivals = None
        
        self.event_list_empty = False
        self.max_time = max_time

        self.run()


    def event_I(self,curr_event):
        time = curr_event["time"]

        # Action
        
        self.num_total_arrivals = 0
        self.num_line_checkin_inside = 0
        self.num_line_checkin_outside = 0
        self.num_line_camera = 0
        self.num_line_clerk = 0
        self.num_line_roadtest = 0
        self.num_line_writtentest = 0
        self.num_line_cashier = 0
        
        # Queue P, initial 
        temp = {}
        temp["time"] = 0
        temp["event"] = "P"
        self.time_events_list.addNode(temp["time"], temp)
            
        # Queue A
        t_a = self.rng_generator.exponential(1 / self.arrival_rate)
        temp = {}
        temp["time"] = time + t_a
        temp["event"] = "A"
        self.time_events_list.addNode(temp["time"], temp)

        # Log        
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_line_checkin_inside"] = self.num_line_checkin_inside
        curr_event["num_line_checkin_outside"] = self.num_line_checkin_outide
        curr_event["num_line_camera"] = self.num_line_camera
        curr_event["num_line_clerk"] = self.num_line_clerk
        curr_event["num_line_roadtest"] = self.num_line_roadtest
        curr_event["num_line_writtentest"] = self.num_line_writtentest
        curr_event["num_line_cashier"] = self.num_line_cashier
        
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)
        
    def event_P(self,curr_event):
        time = curr_event["time"]
        self.num_total_arrivals += 1

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
            if time_of_day > 16 and time_of_day < 18:
                t_a = self.rng_generator.exponential(1 / self.increased_arrival_rate)
            else:
                t_a = self.rng_generator.exponential(1 / self.arrival_rate)
        if time + t_a <= self.max_time:
            temp = {}
            temp["time"] = time + t_a
            temp["event"] = "A"
            self.time_events_list.addNode(temp["time"], temp)

        # Log
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_line_checkin_inside"] = self.num_line_checkin_inside
        curr_event["num_line_checkin_outside"] = self.num_line_checkin_outide
        curr_event["num_line_camera"] = self.num_line_camera
        curr_event["num_line_clerk"] = self.num_line_clerk
        curr_event["num_line_roadtest"] = self.num_line_roadtest
        curr_event["num_line_writtentest"] = self.num_line_writtentest
        curr_event["num_line_cashier"] = self.num_line_cashier
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

    def event_L(self,curr_event):
        time = curr_event["time"]

        # Action
        self.num_current_parked -= 1

        # Log
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_line_checkin_inside"] = self.num_line_checkin_inside
        curr_event["num_line_checkin_outside"] = self.num_line_checkin_outide
        curr_event["num_line_camera"] = self.num_line_camera
        curr_event["num_line_clerk"] = self.num_line_clerk
        curr_event["num_line_roadtest"] = self.num_line_roadtest
        curr_event["num_line_writtentest"] = self.num_line_writtentest
        curr_event["num_line_cashier"] = self.num_line_cashier
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
        elif temp["event" == "P":
            self.event_P(temp)

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
            
    def has_phantom(self):
        # Naive check to ensure no overlapping times, though is incredibly unlikely for non-rounded random variates
        if len(self.df_time_table.duplicated(subset=['time']).unique()) == 2:
            return True
        return False
    
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

    total_run_time = 1440 # in hours
    seed = 53243

    s = Simulation(total_run_time,rng_seed=seed)
    print("With Normal Arrival Rate")
    print("------------------------")
    print(f"a) {s.get_fraction_cars_balked():.3f}")
    print(f"b) {s.get_distr_num_current_parked()}")
    print(f"c) {s.get_avg_num_current_parked():.3f}")
    
    # print(f"Has Phantom) {s.has_phantom()}")     # Was False

    s = Simulation(total_run_time,rng_seed=seed,increased_arrival_rate=12)
    print("\n With Increased Arrival Rate")
    print("---------------------------")
    print(f"a) {s.get_fraction_cars_balked():.3f}")
    print(f"b) {s.get_distr_num_current_parked()}")
    print(f"c) {s.get_avg_num_current_parked():.3f}")
    
    # print(f"Has Phantom) {s.has_phantom()}")    # Was False