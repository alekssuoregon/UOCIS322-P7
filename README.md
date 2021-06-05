# UOCIS322 - Project 7 #

Author: Aleksandr Stevens

Contact: alekss@uoregon.edu

Description:
This website offers a system for calculating open and close times for a brevet control based on the input time and distance of the control. 
All interactivity is done using javascript and AJAX. Whenever a new entry is made, the javascript sends the request to the flask server
to run the computation and returns the result as a JSON message. The algorithm used to calculate the open and close times is defined
here https://rusa.org/pages/acp-brevet-control-times-calculator.

Functionality is also provided to write and retrieve brevets from a MongoDB database. The 'Submit' button will store your brevet in the database as long as it 1.) Doesn't have repeat controls 2.) Controls are in order and 3.) The form is not empty. The 'Display' button will then open a new tab showing all past stored brevets.

An additional website provides a client interface for interacting with stored brevets. A username and password system is in place here that uses Flask-Login and Flask-WTF along with a token authentication system.

Finally, an API is provided to retrieve data from the MongoDB database that stores the brevets. The possible queries are:

1.) /listAll - this returns all brevets

2.) /listOpenOnly - this returns all brevets without the close times in the controls

3.) /listCloseOnly - this returns all brevets without the open times in the controls

4.) /register - registers a user using the provided username and password

5.) /token - returns a token to authenticate operations 1,2 or 3

Each query can also be modified with the /json or /csv directive to specify a specific return format. the ?top=N variable can also be used to limit the number of controls you want returned for each brevet. It will return the first N controls for each brevet.

Edge Cases:

This part defines special cases not outlined in the rusa.org documentation and how it is handled here.

1.) If the brevet control is at distance 0-60. Then the open time will be unchanged and closed time will be calculated at 20km/hr + 1hr 

2.) If the brevet control is on a boundary(200, 400, 600, 10000), then it will fall within the lower ranges ruleset.

3.) In calculations, hours are truncated and minutes are rounded up for the open and close times 
