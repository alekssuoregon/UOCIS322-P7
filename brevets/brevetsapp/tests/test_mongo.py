"""
Nose tests for mongodb 
"""

import nose    # Testing framework
import logging
import os
from pymongo import MongoClient
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.WARNING)
log = logging.getLogger(__name__)

#Test to see if basic insert, retrieve, and delete functionality works in pymongo
def test_mongodb():
    client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
    db = client.testdb
    entry_id = db.testdb.insert_one({'test': True})
    retrieved = db.testdb.find_one_and_delete({'test': True})
    assert retrieved['test'] == True

    retrieved = db.testdb.find_one({'test': True})
    assert retrieved == None


