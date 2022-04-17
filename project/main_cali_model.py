import numpy as np
import numpy.random as rand
import pandas as pd
from sorted_linked_list import LinkedList
from numpy.random import default_rng

# Done:
# - Remodeled system to math that of a californian DMV. See powerpoint slide for updated model
# - got better estimates for transition probabilities, arrival rate see .ipynb
# - Got rid of allocation policy -> Changed these to be inputs to the model.
# - Changed rates to avg time to complete for better estimation
# - Changed nonempty conditions to be random normal mean = 50, std = 10

# To do:
# - line 264 -> should we be using the P event?
# - P events
#       - LinkedList: Add priority P > B for initial processing, both have time 0
#       - test with 0 people starting in line. Does it work as expected?
#       - Same P event logged twice during the last two events of the initial let in.
# - Doesn't run for multiple days
# - How to track output metrics
#       Average wait time
#       Average number of people
#       Max number of people in each line
# check Percent fails = 1/3
# check avg arrivals per day is = 137

# Overall Notes
# - Time is in hours, max_days is days
# - Slide 117 of Chapter 1 has the event graph for multi-server; it was helpful to make sure stuff is being tracked correctly
# - XP added some general comments to Project Proposal document about flow of customers

class Simulation():
    def __init__(self, max_days = 120, rng_seed = None,
                 inside_capacity = 25,idle_checkin_servers = 3,idle_camera_servers = 2,
                 idle_roadtest_servers = 7,idle_writtentest_servers = 8,idle_clerk_servers = 20,
                 idle_cashier_servers = 3):

        self.rng_generator = default_rng(rng_seed)
        self.master_df_time_table = pd.DataFrame() # Each daily data is appended
        self.time_events_list = LinkedList()
        
        # How long each process takes
        self.checkin_avg_time = 1 / 60
        self.roadtest_avg_time = 20 / 60
        self.camera_avg_time = 1 / 60
        self.clerk_avg_time = 15 / 60
        self.writtentest_avg_time = 5 / 60
        self.cashier_avg_time = 1 / 60

        # Increased arrival rates. 7:30-5:00 workday assuming. In hours
        self.morning_rush_end = 0.5  # until 8:00
        self.lunch_rush_start = 3.5  # 11:00 start
        self.lunch_rush_end = 6.5  # 2:00 end
        self.workday_length = 9.5  # Close at 5:00
        self.decreased_arrival_rate = 115
        self.increased_arrival_rate = 175

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
        
        # Dataframe table for each day 
        self.df_time_table = pd.DataFrame()

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
        
        self.num_to_initially_letinside = 0 # Number of people to let in when doors open, including those who will be served
        self.num_to_initially_serve = 0 # Number of people to let in and serve when doors open


        self.num_line_checkin_outside = self.rng_generator.normal(50,10)
        self.num_total_arrivals += self.num_line_checkin_outside
        
        
                
        # Queue P, initial processing of letting people and assigning a server if open
        if self.num_line_checkin_outside <= self.idle_checkin_servers: # Fewer people outside than servers
            self.num_to_initially_serve = self.num_line_checkin_outside
            self.num_to_initially_letinside = self.num_to_initially_serve
            
        elif self.num_line_checkin_outside <= self.inside_capacity + self.idle_checkin_servers:
            self.num_to_initially_serve = self.idle_checkin_servers
            self.num_to_initially_letinside = self.num_line_checkin_outside
            
        else: # When there are more people outside than servers and inside capacity
            self.num_to_initially_serve = self.idle_checkin_servers
            self.num_to_initially_letinside = self.inside_capacity + self.num_to_initially_serve
                    
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
        M = 1000
        temp = {}
        temp["time"] = time + M # far enough into the future such that it will be the last event
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
        self.num_total_arrivals += 0 # Already accounted for in event_I for simplicity
        # todo get rid of this?
        
        
        # Mode 1: let all people inside the building
        if self.num_to_initially_letinside >= 1:
            # Action
            self.num_to_initially_letinside -= 1
            self.num_line_checkin_outside -= 1
            self.num_line_checkin_inside += 1
            
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
            if self.num_to_initially_serve > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "P"
                self.time_events_list.addNode(temp["time"], temp)
            if self.num_to_initially_serve >= 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CI"
                self.time_events_list.addNode(temp["time"], temp)                      
            
        # Log
        self.log(curr_event)
        
        
        
    def event_A(self,curr_event):
        '''Arrival of a new customer to the DMV'''
        
        time = curr_event["time"]

        # Action
        self.num_total_arrivals += 1
        
        if self.num_line_checkin_inside < self.inside_capacity:
            self.num_line_checkin_inside += 1
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
        
        # Let someone inside if someone is waiting outside
        if self.num_line_checkin_outside > 0:
            self.num_line_checkin_outside -= 1
            self.num_line_checkin_inside += 1

        # Queue an End Check-in
        temp = {}
        t_ci = self.rng_generator.exponential(self.checkin_avg_time)
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
            if self.idle_writtentest_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_WT"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk:
            self.num_line_clerk += 1
            if self.idle_clerk_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CLK"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk+self.p_checkin_camera:
            self.num_line_camera += 1
            if self.idle_camera_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CAM"
                self.time_events_list.addNode(temp["time"], temp)
        elif rng < self.p_checkin_written+self.p_checkin_clerk+self.p_checkin_camera+\
                self.p_checkin_driving:
            self.num_line_roadtest += 1
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

        # Queue an End Camera
        temp = {}
        t_cam = self.rng_generator.exponential(self.camera_avg_time)
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

        # Queue an End Clerk
        temp = {}
        t_clk = self.rng_generator.exponential(self.clerk_avg_time)
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

        # Queue an End Road Test
        temp = {}
        t_rt = self.rng_generator.exponential(self.roadtest_avg_time)
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
            if self.idle_cashier_servers > 0:
                temp = {}
                temp["time"] = time
                temp["event"] = "B_CSH"
                self.time_events_list.addNode(temp["time"], temp)
        else:
            self.num_line_camera += 1
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

        # Queue an End Written Test
        temp = {}
        t_wt = self.rng_generator.exponential(self.writtentest_avg_time)
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

        # Queue an End Check-in
        temp = {}
        t_csh = self.rng_generator.exponential(self.cashier_avg_time)
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
        
        # Store today's results to the master table
        self.master_df_time_table = self.master_df_time_table.append(self.df_time_table, ignore_index=True)
        
        # Increment day_counter
        self.day_counter += 1
        
        # If there are more days to simulate, add event_I to events list to initialize new day
        # Don't think can call run() again because it will call run() inside original run()
        if self.day_counter < self.max_days:
            temp = {}
            temp["time"] = 0
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


if __name__ == "__main__":

    max_days = 1
    seed = 53243

    s = Simulation(max_days = max_days, rng_seed = seed,idle_checkin_servers = 30)
    print(s.master_df_time_table)
    
    # print(f"Has Phantom) {s.has_phantom()}")     # Was False