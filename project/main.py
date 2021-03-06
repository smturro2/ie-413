import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList
from numpy.random import default_rng
import matplotlib.pyplot as plt
import scipy.stats as stats

# Done:
# - Rounded initial arrivals
# - P events
#       - LinkedList: Add priority P > B for initial processing, both have time 0 - NOT DONE EXPLICITLY BUT WORKS
#       - test with 0 people starting in line. Does it work as expected? - Works for starting = 0, <
#       - Same P event logged twice during the last two events of the initial let in. - Reversed order of B_CI and P so looks better
# - END_DAY functional, runs multiple days using a 100*day_counter ticker
# - Output metrics done
# - Finalize estimates for service times and number of servers
# - initial arrivals now arrive spaced out.
# - conf intervals calculated


class Simulation():
    def __init__(self, max_days = 120, rng_seed = None,
                 inside_capacity = 30,idle_checkin_servers = 4,idle_camera_servers = 1,
                 idle_roadtest_servers = 4,idle_writtentest_servers = 30,idle_clerk_servers = 14,
                 idle_cashier_servers = 3, plot_output = False):

        self.rng_generator = default_rng(rng_seed)
        self.master_df_time_table = pd.DataFrame() # Each daily data is appended
        self.master_output_table = pd.DataFrame() # Each daily data outputs are appended
        self.time_events_list = LinkedList()
        
        # How long each process takes
        self.checkin_avg_time = 1.5 / 60
        self.roadtest_avg_time = 15 / 60
        self.camera_avg_time = 1.5 / 60
        self.clerk_avg_time = 10 / 60
        self.writtentest_avg_time = 30 / 60
        self.cashier_avg_time = 1 / 60

        # Increased arrival rates. 7:30-5:00 workday assuming. In hours
        self.morning_rush_end = 0.5  # until 8:00
        self.lunch_rush_start = 3.5  # 11:00 start
        self.lunch_rush_end = 6.5  # 2:00 end
        self.workday_length = 9.5  # Close at 5:00
        self.initial_arrival_rate = 50
        self.decreased_arrival_rate = 115
        self.increased_arrival_rate = 162

        # Probability of moving from *** to ***
        a=0.0645375
        self.p_checkin_written= .408*(1 - a)
        self.p_checkin_clerk= .336*(1 - a)
        self.p_checkin_camera= .137*(1 - a)
        self.p_checkin_driving= .119*(1 - a)
        self.p_checkin_fail= a
        self.p_written_fail= .55
        self.p_road_fail= .456
        self.p_clerk_fail= a/4

        # Number of servers
        self.inside_capacity = inside_capacity
        self.idle_checkin_servers = idle_checkin_servers
        self.idle_camera_servers = idle_camera_servers
        self.idle_roadtest_servers = idle_roadtest_servers
        self.idle_writtentest_servers = idle_writtentest_servers
        self.idle_clerk_servers = idle_clerk_servers
        self.idle_cashier_servers = idle_cashier_servers

        
        # Others
        self.event_list_empty = False
        self.max_days = max_days
        self.day_counter = 0 
        self.m = 100 # day modulus to differentiate time of each day
        self.plot_output = plot_output

        
        print(f'Running Simulation for {self.max_days} days...')

        self.run()


    def log(self,curr_event):
        curr_event["num_total_arrivals"] = self.num_total_arrivals
        curr_event["num_line_checkin_inside"] = self.num_line_checkin_inside
        curr_event["num_line_checkin_outside"] = self.num_line_checkin_outside
        curr_event["num_line_camera"] = self.num_line_camera
        curr_event["num_line_clerk"] = self.num_line_clerk
        curr_event["num_line_roadtest"] = self.num_line_roadtest
        curr_event["num_line_writtentest"] = self.num_line_writtentest
        curr_event["num_line_cashier"] = self.num_line_cashier
        curr_event["num_fails"] = self.num_fails
        curr_event["day_counter"] = self.day_counter
        self.df_time_table = self.df_time_table.append(curr_event, ignore_index=True)

        
        
    def event_I(self,curr_event):
        '''Initialization event, marking the beginning of a new day. Resets variables that reset per day'''
        time = curr_event["time"]
        
        print(f'Beginning day {self.day_counter}...')
        
        # Dataframe table for each day 
        self.df_time_table = pd.DataFrame()

        # Queue arrival and departure times
        self.queue_times = {}
        queues = ["outside","inside","wt","rt","cam","clk","csh"]
        for q in queues:
            for i in ["arrive","depart"]:
                self.queue_times[q+"_"+i] = list()

        # Service times
        self.service_times = {}
        servers = ["ci","wt","rt","cam","clk","csh"]
        for s in servers:
            self.service_times[s] = list()
        
        # Action
        self.num_total_arrivals = 0
        self.num_line_checkin_inside = 0
        self.num_line_checkin_outside = 0
        self.num_line_camera = 0
        self.num_line_clerk = 0
        self.num_line_roadtest = 0
        self.num_line_writtentest = 0
        self.num_line_cashier = 0
        self.num_fails = 0
        
        ###
        # Fix times to be scaled based on day_counter for determing arrival cutoff times
        ###
        self.morning_rush_end = 0.5 + self.m*self.day_counter # until 8:00
        self.lunch_rush_start = 3.5 + self.m*self.day_counter # 11:00 start
        self.lunch_rush_end = 6.5 + self.m*self.day_counter # 2:00 end
        self.workday_length = 9.5 +self.m*self.day_counter # Close at 5:00
        
        self.num_to_initially_letinside = 0 # Number of people to let in when doors open, including those who will be served
        self.num_to_initially_serve = 0 # Number of people to let in and serve when doors open

        # Initial arrivals before doors open
        #time_init = 0
        #while time_init > -1:
        time_init = self.day_counter * self.m
        cutoff = time_init - 1
        while time_init > cutoff:
            time_init -= self.rng_generator.exponential(1 / self.initial_arrival_rate)
            self.num_line_checkin_outside += 1
            self.queue_times["outside_arrive"].append(time_init)
        self.num_total_arrivals += self.num_line_checkin_outside
                
        # Queue P, initial processing of letting people and assigning a server if open
        if self.num_line_checkin_outside <= self.idle_checkin_servers: # Fewer people outside than servers
            self.num_to_initially_serve = self.num_line_checkin_outside
            self.num_to_initially_letinside = self.num_to_initially_serve
            
        elif self.num_line_checkin_outside < self.inside_capacity:
            self.num_to_initially_serve = self.idle_checkin_servers
            self.num_to_initially_letinside = self.num_line_checkin_outside
            
        else: # When there are more people outside than servers and inside capacity
            self.num_to_initially_serve = self.idle_checkin_servers
            self.num_to_initially_letinside = self.inside_capacity
                    
        if self.num_to_initially_serve >= 1:
            temp = {}
            temp["time"] = time
            temp["event"] = "P"
            self.time_events_list.addNode(temp["time"], temp)
            
            
            
        # Queue A
        t_a = self.rng_generator.exponential(1 / self.increased_arrival_rate)
        temp = {}
        temp["time"] = time + t_a
        temp["event"] = "A"
        self.time_events_list.addNode(temp["time"], temp)
        
        # Queue END_DAY
        temp = {}
        temp["time"] = time + self.m # far enough into the future such that it will be the last event
        temp["event"] = "END_DAY"
        self.time_events_list.addNode(temp["time"], temp)

        # Log        
        self.log(curr_event)
        
        
        
    def event_P(self,curr_event):
        '''Process people waiting outside when doors open. 
        There are two parts: letting people in to be served and letting people inside.
        First, let in all people to building below capacity, including those who will be served. 
        Then, assign a server to people who can be served. Note: checkin_inside will decrement at begin service'''
        
        time = curr_event["time"]
        
        # Action        
        
        # Mode 1: let all people inside the building
        if self.num_to_initially_letinside >= 1:
            # Action
            self.num_to_initially_letinside -= 1
            self.num_line_checkin_outside -= 1
            self.num_line_checkin_inside += 1
            # Add queue arrivals/departures to list
            self.queue_times["outside_depart"].append(time)
            self.queue_times["inside_arrive"].append(time)

            # Schedule more events
            if self.num_to_initially_letinside > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "P"
                self.time_events_list.addNode(temp["time"], temp)
                
        # Mode 2: No more people to let inside building, assign servers to those inside
        if self.num_to_initially_letinside == 0 and self.num_to_initially_serve >= 1:
            # Action
            self.num_to_initially_serve -= 1
            
            # Schedule more events
            if self.num_to_initially_serve >= 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CI"
                self.time_events_list.addNode(temp["time"], temp)  
            if self.num_to_initially_serve > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "P"
                self.time_events_list.addNode(temp["time"], temp)
                    
            
        # Log
        self.log(curr_event)
        
        
        
    def event_A(self,curr_event):
        '''Arrival of a new customer to the DMV'''
        
        time = curr_event["time"]

        # Action
        self.num_total_arrivals += 1
        # Add queue arrivals/departures to list
        self.queue_times["outside_arrive"].append(time)
        
        if self.num_line_checkin_inside < self.inside_capacity:
            self.num_line_checkin_inside += 1
            self.queue_times["outside_depart"].append(time)
            self.queue_times["inside_arrive"].append(time)
        else:
            self.num_line_checkin_outside += 1

        # Determine t_a based on rush times 
        if time <= self.morning_rush_end or (self.lunch_rush_start < time and time <= self.lunch_rush_end):
            t_a = self.rng_generator.exponential(1 / self.increased_arrival_rate)
        else:
            t_a = self.rng_generator.exponential(1 / self.decreased_arrival_rate)
            
        # Queue another A if it would fall before end of workday
        if time + t_a <= self.workday_length: # similar to cancelling arrival 
            temp = {}
            temp["time"] = time + t_a
            temp["event"] = "A"
            self.time_events_list.addNode(temp["time"], temp)
            
        # Queue a begin check in if there is an idle server
        if self.idle_checkin_servers > 0:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CI"
            self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
        
        
        
    def event_B_CI(self,curr_event):
        '''Begin Check-in'''
        
        time = curr_event["time"]
        
        # Action
        self.idle_checkin_servers -= 1
        self.num_line_checkin_inside -= 1
        # Add queue arrivals/departures to list
        self.queue_times["inside_depart"].append(time)
        
        # Let someone inside if someone is waiting outside
        if self.num_line_checkin_outside > 0:
            self.num_line_checkin_outside -= 1
            self.num_line_checkin_inside += 1
            self.queue_times["outside_depart"].append(time)
            self.queue_times["inside_arrive"].append(time)

        # Queue an End Check-in
        temp = {}
        t_ci = self.rng_generator.exponential(self.checkin_avg_time)
        # Record service time
        self.service_times["ci"].append(t_ci)
        temp["time"] = time + t_ci
        temp["event"] = "E_CI"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
        
        

    def event_E_CI(self,curr_event):
        '''End Check-in'''
        
        time = curr_event["time"]

        # Action
        self.idle_checkin_servers += 1

        # Queue up more immediately if there is a line
        if self.num_line_checkin_inside >= self.idle_checkin_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CI"
            self.time_events_list.addNode(temp["time"], temp)
            
        # Transfer customer to wt, clerk, camera, driving, or fail
        rng = self.rng_generator.random()
        if rng < self.p_checkin_written:
            self.num_line_writtentest += 1
            # Add queue arrivals/departures to list
            self.queue_times["wt_arrive"].append(time)
            if self.idle_writtentest_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_WT"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk:
            self.num_line_clerk += 1
            # Add queue arrivals/departures to list
            self.queue_times["clk_arrive"].append(time)
            if self.idle_clerk_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CLK"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk+self.p_checkin_camera:
            self.num_line_camera += 1
            # Add queue arrivals/departures to list
            self.queue_times["cam_arrive"].append(time)
            if self.idle_camera_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CAM"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk+self.p_checkin_camera+\
                self.p_checkin_driving:
            self.num_line_roadtest += 1
            # Add queue arrivals/departures to list
            self.queue_times["rt_arrive"].append(time)
            if self.idle_roadtest_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_RT"
                self.time_events_list.addNode(temp["time"], temp)

        else:
            # Failed
            self.num_fails += 1

        # Log
        self.log(curr_event)
        
        
        
    def event_B_CAM(self,curr_event):
        '''Begin camera event'''
        
        time = curr_event["time"]
        
        # Action
        self.idle_camera_servers -= 1
        self.num_line_camera -= 1
        # Add queue arrivals/departures to list
        self.queue_times["cam_depart"].append(time)

        # Queue an End Camera
        temp = {}
        t_cam = self.rng_generator.exponential(self.camera_avg_time)
        # Record service time
        self.service_times["cam"].append(t_cam)
        temp["time"] = time + t_cam
        temp["event"] = "E_CAM"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_E_CAM(self,curr_event):
        '''End camera event'''
        time = curr_event["time"]

        # Action
        self.idle_camera_servers += 1

        # Queue up more immediately if there is a line
        if self.num_line_camera >= self.idle_camera_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CAM"
            self.time_events_list.addNode(temp["time"], temp)
            
        # Transfer to clerk
        self.num_line_clerk += 1
        # Add queue arrivals/departures to list
        self.queue_times["clk_arrive"].append(time)
        if self.idle_clerk_servers > 0:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CLK"
            self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_B_CLK(self,curr_event):
        '''Begin clerk event'''
        
        time = curr_event["time"]
        
        # Action
        self.idle_clerk_servers -= 1
        self.num_line_clerk -= 1
        # Add queue arrivals/departures to list
        self.queue_times["clk_depart"].append(time)

        # Queue an End Clerk
        temp = {}
        t_clk = self.rng_generator.exponential(self.clerk_avg_time)
        # Record service time
        self.service_times["clk"].append(t_clk)
        temp["time"] = time + t_clk
        temp["event"] = "E_CLK"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_E_CLK(self,curr_event):
        '''End clerk event'''
        time = curr_event["time"]

        # Action
        self.idle_clerk_servers += 1
        if self.num_line_clerk >= self.idle_clerk_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CLK"
            self.time_events_list.addNode(temp["time"], temp)

        # Transfer to cashier or fail
        rng = self.rng_generator.random()
        if rng < self.p_clerk_fail:
            # Fail
            self.num_fails += 1
        else:
            self.num_line_cashier += 1
            # Add queue arrivals/departures to list
            self.queue_times["csh_arrive"].append(time)
            if self.idle_cashier_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CSH"
                self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
        
        
        
    def event_B_RT(self,curr_event):
        '''Begin road test event'''
        
        time  = curr_event["time"]
        
        # Action
        self.idle_roadtest_servers -= 1
        self.num_line_roadtest -= 1
        # Add queue arrivals/departures to list
        self.queue_times["rt_depart"].append(time)

        # Queue an End Road Test
        temp = {}
        t_rt = self.rng_generator.exponential(self.roadtest_avg_time)
        # Record service time
        self.service_times["rt"].append(t_rt)
        temp["time"] = time + t_rt
        temp["event"] = "E_RT"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_E_RT(self,curr_event):
        '''End road test event'''
        
        time = curr_event["time"]

        # Action
        self.idle_roadtest_servers += 1

        # Queue up more immediately if there is a line
        if self.num_line_roadtest >= self.idle_roadtest_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_RT"
            self.time_events_list.addNode(temp["time"], temp)


            
        # Transfer to photo or fail and pay
        rng = self.rng_generator.random()
        if rng < self.p_road_fail:
            # Fail
            self.num_fails += 1
            self.num_line_cashier += 1
            # Add queue arrivals/departures to list
            self.queue_times["csh_arrive"].append(time)
            if self.idle_cashier_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CSH"
                self.time_events_list.addNode(temp["time"], temp)
        else:
            self.num_line_camera += 1
            # Add queue arrivals/departures to list
            self.queue_times["cam_arrive"].append(time)
            if self.idle_camera_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CAM"
                self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_B_WT(self,curr_event):
        '''Begin written test event'''
        
        time = curr_event["time"]
        
        # Action
        self.idle_writtentest_servers -= 1
        self.num_line_writtentest -= 1
        # Add queue arrivals/departures to list
        self.queue_times["wt_depart"].append(time)

        # Queue an End Written Test
        temp = {}
        t_wt = self.rng_generator.exponential(self.writtentest_avg_time)
        # Record service time
        self.service_times["wt"].append(t_wt)
        temp["time"] = time + t_wt
        temp["event"] = "E_WT"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_E_WT(self,curr_event):
        '''End written test event'''
        
        time = curr_event["time"]

        # Action
        self.idle_writtentest_servers += 1

        # Queue up more immediately if there is a line
        if self.num_line_writtentest >= self.idle_writtentest_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_WT"
            self.time_events_list.addNode(temp["time"], temp)

        # Always transfer to cashier, sometimes fail
        rng = self.rng_generator.random()
        if rng < self.p_written_fail:
            # Fail
            self.num_fails += 1
        self.num_line_cashier += 1
        # Add queue arrivals/departures to list
        self.queue_times["csh_arrive"].append(time)
        if self.idle_cashier_servers > 0:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CSH"
            self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_B_CSH(self,curr_event):
        '''Begin cashier event'''
        
        time = curr_event["time"]
        
        # Action
        self.idle_cashier_servers -= 1
        self.num_line_cashier -= 1
        # Add queue arrivals/departures to list
        self.queue_times["csh_depart"].append(time)

        # Queue an End Check-in
        temp = {}
        t_csh = self.rng_generator.exponential(self.cashier_avg_time)
        # Record service time
        self.service_times["csh"].append(t_csh)
        temp["time"] = time + t_csh
        temp["event"] = "E_CSH"
        self.time_events_list.addNode(temp["time"], temp)

        # Log
        self.log(curr_event)
    
    
    
    def event_E_CSH(self,curr_event):
        '''End cashier event'''
        
        time = curr_event["time"]

        # Action
        self.idle_cashier_servers += 1

        # Queue up more immediately if there is a line
        if self.num_line_cashier >= self.idle_cashier_servers:
            temp = {}
            temp["time"] = time
            temp["event"] = "B_CSH"
            self.time_events_list.addNode(temp["time"], temp)
            
        # Customer exits system after cashier

        # Log
        self.log(curr_event)
        
        
        
    def event_END_DAY(self,curr_event):
        '''Formal event to end the day, which will then start a new day if less than max days'''
        
        print(f'Ending day {self.day_counter}...')
        
        # Log, store results of just-finished day
        self.log(curr_event)
        
        # Store today's results to the master table
        self.master_df_time_table = self.master_df_time_table.append(self.df_time_table, ignore_index=True)
        # Store avg weight times
        self.master_output_table = self.master_output_table.append(self.get_outputs(), ignore_index=True)
        # Plot daily output
        if self.plot_output:
            self.plot_daily_output()


        # Increment day_counter
        self.day_counter += 1
        
        # If there are more days to simulate, add event_I to events list to initialize new day
        if self.day_counter < self.max_days:
            temp = {}
            temp["time"] = self.m * self.day_counter
            temp["event"] = "I"
            self.time_events_list.addNode(temp["time"],temp)
            
        
        
    def update(self):
        # Get next event
        temp = self.time_events_list.head.data
        if temp["event"] == "A":
            self.event_A(temp)
        elif temp["event"] == "I":
            self.event_I(temp)
        elif temp["event"] == "P":
            self.event_P(temp)
        elif temp["event"] == "B_CI":
            self.event_B_CI(temp)
        elif temp["event"] == "E_CI":
            self.event_E_CI(temp)
        elif temp["event"] == "B_CAM":
            self.event_B_CAM(temp)
        elif temp["event"] == "E_CAM":
            self.event_E_CAM(temp)
        elif temp["event"] == "B_CLK":
            self.event_B_CLK(temp)
        elif temp["event"] == "E_CLK":
            self.event_E_CLK(temp)
        elif temp["event"] == "B_RT":
            self.event_B_RT(temp)
        elif temp["event"] == "E_RT":
            self.event_E_RT(temp)
        elif temp["event"] == "B_WT":
            self.event_B_WT(temp)
        elif temp["event"] == "E_WT":
            self.event_E_WT(temp)
        elif temp["event"] == "B_CSH":
            self.event_B_CSH(temp)
        elif temp["event"] == "E_CSH":
            self.event_E_CSH(temp)
        elif temp["event"] == "END_DAY":
            self.event_END_DAY(temp)

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

    def get_outputs(self):
        queues = ["outside", "inside", "wt", "rt", "cam", "clk", "csh"]
        outputs = {}
        alpha = -1
        mean_service_times = {"outside": self.checkin_avg_time,
                     "inside": self.checkin_avg_time,
                     "wt": self.writtentest_avg_time,
                     "rt": self.roadtest_avg_time,
                     "cam": self.camera_avg_time,
                     "clk": self.clerk_avg_time,
                     "csh": self.cashier_avg_time}
        
        for q in queues:

            outputs["wait_time_"+q] = np.array(self.queue_times[q + "_depart"]) - self.queue_times[q + "_arrive"]
            if q == 'outside' or q == 'inside':
                outputs["wait_time_"+q] = np.array(outputs["wait_time_"+q]) + alpha * (
                                                np.array(self.service_times["ci"]) - mean_service_times[q])
            else:  
                outputs["wait_time_"+q] = np.array(outputs["wait_time_"+q]) + alpha * (
                                                np.array(self.service_times[q]) - mean_service_times[q])
            outputs["wait_time_"+q] = outputs["wait_time_"+q].mean()

        # total
        outputs["wait_time_total"] = outputs["wait_time_outside"] + outputs["wait_time_inside"] +\
                                  self.checkin_avg_time
        outputs["wait_time_total"] += self.p_checkin_written * (outputs["wait_time_wt"]+
                                                             self.writtentest_avg_time +
                                                             outputs["wait_time_csh"] +
                                                             self.cashier_avg_time)
        outputs["wait_time_total"] += self.p_checkin_clerk * (outputs["wait_time_clk"]+
                                                             self.clerk_avg_time +
                                                           (1-self.p_clerk_fail)*(
                                                             outputs["wait_time_csh"] +
                                                             self.cashier_avg_time)
                                                           )
        outputs["wait_time_total"] += self.p_checkin_camera * (outputs["wait_time_cam"]+
                                                             self.camera_avg_time +
                                                           (1-self.p_clerk_fail)*(
                                                             outputs["wait_time_csh"] +
                                                             self.cashier_avg_time)
                                                           )
        outputs["wait_time_total"] += self.p_checkin_driving * (outputs["wait_time_rt"]+
                                                             self.roadtest_avg_time +
                                                             outputs["wait_time_csh"] +
                                                             self.cashier_avg_time +
                                                             (1-self.p_road_fail)*
                                                             (outputs["wait_time_cam"] +
                                                              self.camera_avg_time +
                                                              (1 - self.p_clerk_fail) * (
                                                                      outputs["wait_time_csh"] +
                                                                      self.cashier_avg_time)
                                                              )
                                                             )
        outputs["total_arrivals"] = self.df_time_table.iloc[-1]["num_total_arrivals"]
        outputs["total_fails"] = self.df_time_table.iloc[-1]["num_fails"]
        self.df_distr = self.df_time_table[self.df_time_table.columns[3:-2]][:-1]
        self.df_distr["weights"] = self.df_time_table["time"].diff()[1:].reset_index(drop=True)
        self.df_distr["weights"] = self.df_distr["weights"] / self.df_distr["weights"].sum()
        for c in self.df_distr.columns[:-1]:
            outputs["avg_"+c] = np.dot(self.df_distr[c],self.df_distr["weights"])
            outputs["max_"+c] = np.max(self.df_distr[c])
        outputs["system_empty"] = self.df_time_table.iloc[-2,0] - self.df_time_table.iloc[0,0]    
                    
        return outputs
    
    def plot_daily_output(self, when ='all'):
        last_arrival_index = self.df_time_table.loc[self.df_time_table["event"] == 'A'].tail(1).index.to_list()[0]
        
        #df_distr_time = self.df_time_table.join(self.df_distr)
        df_distr_time = self.df_distr.copy()
        df_distr_time['time'] = self.df_time_table['time'].copy()

        if when == 'before':
            df_distr_time = df_distr_time.iloc[:last_arrival_index]
        elif when == 'after':
            df_distr_time = df_distr_time.iloc[last_arrival_index:]
        elif when == 'all':
            pass
        
        df_distr_time['adj_time'] = df_distr_time['time'] - self.m * self.day_counter
        
        if when == 'before':
            # Before doors close
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_checkin_inside'], label='CI_Inside')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_clerk'], label='Clerk')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_roadtest'], label='Road')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_writtentest'], label='Written')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_cashier'], label='Cashier')
        
        else:
            # After doors close
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_checkin_inside'], label='CI_Inside')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_clerk'], label='Clerk')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_roadtest'], label='Road')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_writtentest'], label='Written')
            plt.plot(df_distr_time['adj_time'], df_distr_time['num_line_cashier'], label='Cashier')
            
        # plt.axvline(x = self.workday_length, c='black')
        plt.legend()
        plt.title("Queue lengths vs. Simulation hour")
        plt.xlabel("Simulation hour")
        plt.ylabel("Number of patrons in line")
        
        plt.show()

def calc_conf_intervals(df_master_outputs,alpha = .05):
    z = stats.t.ppf(q=1-alpha/2,df=len(df_master_outputs)-1)
    df_desc = df_master_outputs.describe()
    df_conf = pd.DataFrame(columns = df_desc.columns)
    df_conf.loc["lower"] = df_desc.loc["mean"] - z * df_desc.loc["std"]
    df_conf.loc["upper"] = df_desc.loc["mean"] + z * df_desc.loc["std"]
    return df_conf


if __name__ == "__main__":

    max_days = 365
    seed = 53243

    s = Simulation(max_days = max_days, inside_capacity = 25, rng_seed = seed, idle_checkin_servers = 4, plot_output=False)
    # master time table
    print(s.master_df_time_table)
    # print(s.master_df_time_table.loc[s.master_df_time_table["event"] == 'END_DAY'])
    # print(s.master_df_time_table.loc[s.master_df_time_table["event"] == 'I'])
    # Check arrivals and fail rate
    # print(s.master_output_table["total_arrivals"]) # True average is 1352
    # print(s.master_output_table["total_fails"]/s.master_output_table["total_arrivals"]) # True percent is 1/3
    print(s.master_output_table.T)
    # Save
    s.master_df_time_table.to_csv("time_table.csv",index=False)
    s.master_output_table.to_csv("outputs.csv",index=False)

    # load
    master_df_time_table = pd.read_csv("time_table.csv")
    master_output_table = pd.read_csv("outputs.csv")
    conf_intervals = calc_conf_intervals(master_output_table)
    print(conf_intervals.T)

    # print(f"Has Phantom) {s.has_phantom()}")     # Was False