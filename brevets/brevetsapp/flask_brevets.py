"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import flask
from flask import request
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
import submit
import config
import json
import os

import logging
from pymongo import MongoClient

###
# Globals
###
app = flask.Flask(__name__)
CONFIG = config.configuration()
client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetdb

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')

@app.route("/display")
def display():
    app.logger.debug("Display page entry")
    #Load the display page and fill it with info from the MongoDB database
    return flask.render_template('db.html',
                brevets=list(db.brevets.find()))


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    #Read in all data from JSON request
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    brevet_dist = request.args.get('brevet_dist', type=int)
    start_time_str = request.args.get('start_time', type=str)
    start_time = arrow.get(start_time_str, acp_times.TIME_FORMAT)

    app.logger.debug("km={}".format(km))
    app.logger.debug("request.args: {}".format(request.args))

    #Brevit distance isn't needed for the calculation so 'None' is passed instead
    open_time = acp_times.open_time(km, brevet_dist, start_time).format(acp_times.TIME_FORMAT)
    close_time = acp_times.close_time(km, brevet_dist, start_time).format(acp_times.TIME_FORMAT)
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)

@app.route("/_submit")
def _submit():
    #Read data from MultiDict and parse string entry as JSON
    brevet_entry = json.loads(request.args.get('data', type=str))
    #Process submit request
    response = submit.process_submit(brevet_entry)
    if response['success'] == True:
        db.brevets.insert_one(brevet_entry)
    #Return marshalled data
    return flask.jsonify(response)

#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
