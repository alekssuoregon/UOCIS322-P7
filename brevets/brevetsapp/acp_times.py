"""
Open and close time calculations
for ACP-sanctioned brevets
following rules described at https://rusa.org/octime_alg.html
and https://rusa.org/pages/rulesForRiders
"""
import arrow


#  You MUST provide the following two functions
#  with these signatures. You must keep
#  these signatures even if you don't use all the
#  same arguments.

TIME_FORMAT = 'YYYY-MM-DDTHH:mm'

# Each entry in the control table is of the form (control location(km),
# min speed(km/hr), max speed(km/hr))
CONTROL_TABLE = [(200, 15, 34), (400, 15, 32), (600, 15, 30),
                 (1000, 11.428, 28), (1300, 13.333, 26)]

#Calculates open and closed time for a given control and start time
def _calculate_arrival(start_time, distance):
    closed_delta = 0
    open_delta = 0

    done = False
    i = 0

    #Iterate over control boundary table and accumulate calculated times
    while not done:
        #Figuring out the distance that was traveled for a control boundary 
        rules = CONTROL_TABLE[i]
        control_location = rules[0]
        stretch_dist = 0
        if distance > control_location:
            if control_location == 200:
                stretch_dist = 200
            else:
                stretch_dist = control_location - CONTROL_TABLE[i-1][0] 
        else:
            stretch_dist = distance
            if i != 0:
                stretch_dist -= CONTROL_TABLE[i-1][0]
            done = True

        #Actual delta time calculations
        closed_delta += stretch_dist / rules[1] 
        open_delta += stretch_dist / rules[2]
        i+=1

    #Conversion from hour fractions to hours and minutes
    closed_delta_hours = int(closed_delta)
    closed_delta_minutes = int(round((closed_delta - closed_delta_hours) * 60))

    open_delta_hours = int(open_delta)
    open_delta_minutes = int(round((open_delta - open_delta_hours) * 60))

    #Apply time changes
    open_arrival_time = start_time.shift(hours=+open_delta_hours, minutes=+open_delta_minutes)
    closed_arrival_time = start_time.shift(hours=+closed_delta_hours, minutes=+closed_delta_minutes)
    return (open_arrival_time, closed_arrival_time)

"""
Args:
   control_dist_km:  number, control distance in kilometers
   brevet_dist_km: number, nominal distance of the brevet
       in kilometers, which must be one of 200, 300, 400, 600,
       or 1000 (the only official ACP brevet distances)
   brevet_start_time:  A date object (arrow)
Returns:
   A date object indicating the control open time.
   This will be in the same time zone as the brevet start time.
"""

def open_time(control_dist_km, brevet_dist_km, brevet_start_time):
    if control_dist_km > brevet_dist_km:
        control_dist_km = brevet_dist_km
    arrival_time, _ = _calculate_arrival(brevet_start_time, control_dist_km)
    return arrival_time 
    

"""
Args:
   control_dist_km:  number, control distance in kilometers
      brevet_dist_km: number, nominal distance of the brevet
      in kilometers, which must be one of 200, 300, 400, 600, or 1000
      (the only official ACP brevet distances)
   brevet_start_time:  A date object (arrow)
Returns:
   A date object indicating the control close time.
   This will be in the same time zone as the brevet start time.
"""
def close_time(control_dist_km, brevet_dist_km, brevet_start_time):
    # Edge case where distance traveled is 0
    if control_dist_km <= 60:
        km_per_min = 20 / 60
        delta = (control_dist_km / km_per_min) + 60 
        delta_hours = int(delta / 60)
        delta_minutes = int(round(delta % 60, 0))
        return brevet_start_time.shift(hours=+delta_hours, minutes=+delta_minutes)
    if control_dist_km > brevet_dist_km:
        control_dist_km = brevet_dist_km

    _, arrival_time = _calculate_arrival(brevet_start_time, control_dist_km) 

    #Offset edge cases for 200 and 400
    if control_dist_km == 200 and brevet_dist_km == 200:
        arrival_time = arrival_time.shift(minutes=+10)
    elif control_dist_km == 400 and brevet_dist_km == 400:
        arrival_time = arrival_time.shift(minutes=+20)
    return arrival_time 

