import os
import flask
from flask import Flask, request, make_response
from flask_restful import Resource, Api
from pymongo import MongoClient
import secrets
import hashlib

from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, \
                                BadSignature, SignatureExpired)
import config

app = Flask(__name__)
CONFIG = config.configuration()
app.config['SECRET_KEY'] = CONFIG.SECRET_KEY
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetdb
auth_db = client.auth

EXPIRED_ERR = "expired"
INVALID_ERR = "invalid"
SUCCESS = "success"

MAX_USERS = 10000000

#Converts database records to csv
#Returned as brevet_dist, km, open, close, km, open, close,...
def _db_data_to_csv(data):
    csv_data = ""
    print(data)
    for brevet in data:
        line = ""
        line += brevet['brevet_dist']
        for control in brevet['controls']:
            line += ',' + control['km']
            if 'open' in control: 
                line += ',' + control['open']
            if 'close' in control: 
                line += ',' + control['close']
        csv_data += line + '\n'
    return csv_data

#Strips a brevets controls down to the 'top_n'
def _top_n_list(items, top_n):
    len_items = len(items)
    if top_n > len_items:
        return items

    top_items = items[:top_n]
    return top_items

#applies _top_n_list to each individual brevet
def _top_n_brevet_list(brevets, top_n):
    new_brevets = []
    for brevet in brevets:
        new_brevet = brevet
        new_brevet['controls'] = _top_n_list(brevet['controls'], top_n)
        new_brevets.append(new_brevet)
    return new_brevets

#Strips fields like '_id' from database records
def _strip_database_records(data):
    brevets = []
    for record in data:
        brevet = {'brevet_dist' : record['brevet_dist']}
        controls = []
        for control in record['controls']:
            new_control = {'km': control['km'], 'open': control['open'], 'close': control['close']}
            controls.append(new_control)
        brevet['controls'] = controls
        brevets.append(brevet)
    return brevets

def _generate_token(user_id, expiration=600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id':user_id})

def _validate_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    success = False
    try:
        data = s.loads(token)
        if auth_db.users.find(data) != None:
            success = True
    except SignatureExpired:
        return EXPIRED_ERR 
    except BadSignature:
        return INVALID_ERR

    if success:
        return SUCCESS
    return INVALID_ERR

#Resource for handling listAll requests
class ListAll(Resource):
    def get(self, fmt='json'): 
        #Remove database specific key,value pairs
        brevets = _strip_database_records(list(db.brevets.find()))

        #validate
        token = request.args.get('token', type=str)
        if token == None or _validate_token(token) != SUCCESS:
            return make_response('error:' + INVALID_ERR, 401) 

        validity = _validate_token(token)
        if validity != SUCCESS:
            return make_response('error:' + validity, 401)

        #Remove all controls other than the 'top_n', if applicable
        top_n = request.args.get('top', type=int)
        if top_n != None:
            brevets = _top_n_brevet_list(brevets, top_n)

        #Return either json or csv
        if fmt == 'json':
            return make_response(flask.jsonify(brevets), 200)
        elif fmt == 'csv':
            return make_response(_db_data_to_csv(brevets), 200)
        else:
            return make_response('INVALID FORMAT DIRECTIVE', 401)

#used to remove 'open' or 'closed' from the retrieved database records
def _rm_from_brevets_controls(brevets, key):
    for brevet in brevets:
        for control in brevet['controls']:
            del control[key]
    return brevets

#Resource for handling listOpenOnly requests
class ListOpenOnly(Resource):
    def get(self, fmt='json'):
        brevets = _strip_database_records(list(db.brevets.find()))

        #validate
        token = request.args.get('token', type=str)
        if token == None or _validate_token(token) != SUCCESS:
            return make_response('error:' + INVALID_ERR, 401) 

        validity = _validate_token(token)
        if validity != SUCCESS:
            return make_response('error:' + validity, 401)

        #process
        top_n = request.args.get('top', type=int)
        if top_n != None:
            brevets = _top_n_brevet_list(brevets, top_n)

        brevets = _rm_from_brevets_controls(brevets, 'close')
        if fmt == 'json':
            return make_response(flask.jsonify(brevets), 200)
        elif fmt == 'csv':
            return make_response(_db_data_to_csv(brevets), 200)
        else:
            return make_response('INVALID FORMAT DIRECTIVE', 401)

#Resource for handling listCloseOnly requests
class ListCloseOnly(Resource):
    def get(self, fmt='json'):
        brevets = _strip_database_records(list(db.brevets.find()))

        #validate
        token = request.args.get('token', type=str)
        if token == None or _validate_token(token) != SUCCESS:
            return make_response('error:' + INVALID_ERR, 401) 

        validity = _validate_token(token)
        if validity != SUCCESS:
            return make_response('error:' + validity, 401)

        #process
        top_n = request.args.get('top', type=int)
        if top_n != None:
            brevets = _top_n_brevet_list(brevets, top_n)

        brevets = _rm_from_brevets_controls(brevets, 'open')
        if fmt == 'json':
            return make_response(flask.jsonify(brevets), 200)
        elif fmt == 'csv':
            return make_response(_db_data_to_csv(brevets), 200)
        else:
            return make_response('INVALID FORMAT DIRECTIVE', 401)

class Register(Resource):
    def get(self):
        username = request.args.get('username', type=str)
        passwd = request.args.get('password', type=str)
        app.logger.debug("USERNAME: " + username)
        app.logger.debug("PASSWORD: " + passwd)
        
        #Check for errors
        if username == None or passwd == None:
            resp = flask.jsonify({'error':'Not enough parameters'})
            resp.status_code = 400
            return resp 

        if auth_db.users.find_one({'username': username}) != None:
            resp = flask.jsonify({'error':'User already exists'})
            resp.status_code = 400
            return resp

        #Hash password
        h = hashlib.new('sha512_256')
        h.update(passwd.encode('utf-8'))
        h_pass = h.hexdigest() 

        #insert
        app.logger.debug("STORED_PASS: " + h_pass)
        id_n = secrets.randbelow(MAX_USERS)
        entry = {'id': id_n , 'username': username, 'password': h_pass}
        auth_db.users.insert_one(entry)
        resp_entry = {'id': id_n , 'username': username, 'password': h_pass}

        resp = flask.jsonify(resp_entry)
        resp.status_code = 200

        return resp 

class Token(Resource):
    def get(self):
        #get parameters
        username = request.args.get('username', type=str)
        passwd = request.args.get('password', type=str)

        if username == None or passwd == None:
            resp = flask.jsonify({'error': 'Not enough parameters'})
            resp.status_code = 401
            return resp

        #fetch database entry
        user_info = auth_db.users.find_one({'username':username})
        if user_info == None:
            resp = flask.jsonify({'error': 'Invalid username'})
            resp.status_code = 401
            return resp

        #validate password
        h = hashlib.new('sha512_256')
        h.update(passwd.encode('utf-8'))
        h_pass = h.hexdigest() 
        app.logger.debug("HPASS: " + h_pass + " RPASS: " + user_info['password'])
        if h_pass != user_info['password']:
            resp = flask.jsonify({'error': 'Bad password'})
            resp.status_code = 401
            return resp

        #return token
        token = _generate_token(user_info['id'])
        resp = flask.jsonify({'id': int(user_info['id']), 'token': token.decode('utf-8')})
        resp.status_code = 200
        return resp



#Different possible urls to use for queries
api.add_resource(ListAll, '/listAll', '/listAll/<string:fmt>')
api.add_resource(ListOpenOnly, '/listOpenOnly', '/listOpenOnly/<string:fmt>')
api.add_resource(ListCloseOnly, '/listCloseOnly', '/listCloseOnly/<string:fmt>')
api.add_resource(Register, '/register')
api.add_resource(Token, '/token')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)


