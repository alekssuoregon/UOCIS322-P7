"""
Nose tests for submit.py
"""
import submit 

import nose    # Testing framework
import logging
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.WARNING)
log = logging.getLogger(__name__)

"""
-----------
PLEASE READ
-----------
Please note that the 'submit' function here is responsible for all
logic to process a submit request. The only functionality not included
is the db.brevets.insert_one() function call which is done in the
"/_submit" route in the flask app. I decided to test
the submit logic and not the actual mongodb insertion because writing a 
unit test that just checked if the line 'db.brevets.insert_one()'
succeeded would be a useless test since it's one line calling a
function I didn't even write.
"""

#Test to make sure out of order errors are caught
def test_out_of_order():
    request = {
        'brevet_dist': '200',
        'controls' : [
            {'km': '10', 'open': '', 'close': ''},
            {'km': '5', 'open': '', 'close': ''}
        ]
    }

    response = submit.process_submit(request)
    assert response['success'] == False
    assert response['error'] == "Brevet controls out of order"

#Test to make sure empty request errors are caught
def test_empty():
    request = {
        'brevet_dist': '200',
        'controls' : []
    }

    response = submit.process_submit(request)
    assert response['success'] == False
    assert response['error'] == "No brevet controls input"

