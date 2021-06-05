"""
Nose tests for acp_times.py
"""
import acp_times

import nose    # Testing framework
import logging
import arrow
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.WARNING)
log = logging.getLogger(__name__)

# Tests that basic calculations work
def test_basic_calculate_arrival():
    start_time = arrow.get('2021-01-01T00:00', acp_times.TIME_FORMAT)
    correct_open_time = arrow.get('2021-01-01T09:42', acp_times.TIME_FORMAT)
    correct_closed_time = arrow.get('2021-01-01T21:28', acp_times.TIME_FORMAT)

    open_time, closed_time = acp_times._calculate_arrival(start_time, 322) 
    assert correct_open_time.format(acp_times.TIME_FORMAT) == open_time.format(acp_times.TIME_FORMAT) 
    assert correct_closed_time.format(acp_times.TIME_FORMAT) == closed_time.format(acp_times.TIME_FORMAT) 

# Tests that border value calculations work
def test_border_calculate_arrival():
    start_time = arrow.get('2021-01-01T00:00', acp_times.TIME_FORMAT)
    correct_open_time = arrow.get('2021-01-01T05:53', acp_times.TIME_FORMAT)
    correct_closed_time = arrow.get('2021-01-01T13:20', acp_times.TIME_FORMAT)

    open_time, closed_time = acp_times._calculate_arrival(start_time, 200) 
    assert correct_open_time.format(acp_times.TIME_FORMAT) == open_time.format(acp_times.TIME_FORMAT) 
    assert correct_closed_time.format(acp_times.TIME_FORMAT) == closed_time.format(acp_times.TIME_FORMAT) 

# Tests the a control at zero works(this is an edge case)
def test_zero_closed_time():
    start_time = arrow.get('2021-01-01T00:00', acp_times.TIME_FORMAT)
    correct_closed_time = arrow.get('2021-01-01T01:00', acp_times.TIME_FORMAT)

    closed_time = acp_times.close_time(0, 200, start_time)
    assert correct_closed_time.format(acp_times.TIME_FORMAT) == closed_time.format(acp_times.TIME_FORMAT) 

# Tests that the open_time function works
def test_open_time():
    start_time = arrow.get('2021-01-01T00:00', acp_times.TIME_FORMAT)
    correct_open_time = arrow.get('2021-01-01T01:58', acp_times.TIME_FORMAT)

    open_time = acp_times.open_time(67, 200, start_time) 
    assert correct_open_time.format(acp_times.TIME_FORMAT) == open_time.format(acp_times.TIME_FORMAT) 

# Tests that the close_time function works
def test_close_time():
    start_time = arrow.get('2021-01-01T00:00', acp_times.TIME_FORMAT)
    correct_closed_time = arrow.get('2021-01-01T04:28', acp_times.TIME_FORMAT)

    closed_time = acp_times.close_time(67, 200, start_time) 
    assert correct_closed_time.format(acp_times.TIME_FORMAT) == closed_time.format(acp_times.TIME_FORMAT) 


