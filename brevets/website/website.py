import flask
from flask import Flask, session, request, render_template, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required, login_user, logout_user, UserMixin,
                        confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, SubmitField, PasswordField, validators
import config
import requests
import json
import os
import hashlib
from pymongo import MongoClient
import hashlib
from urllib.parse import urlparse, urljoin


import logging

###
# Globals
###
app = flask.Flask(__name__)
CONFIG = config.configuration()
app.config.from_object(__name__)
app.secret_key = CONFIG.SECRET_KEY

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.refresh_view = "login"
login_manager.needs_refresh_message = ("To protect your account, please reauthenticate to access this page.")
login_manager.needs_refresh_message_category = "info"
login_manager.init_app(app)

#docker-compose environment variables
API_ADDR = os.environ['BACKEND_ADDR']
API_PORT = os.environ['BACKEND_PORT']

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
auth_db = client.auth

##
# Forms
##

class LoginForm(Form):
    username = StringField("Username", [validators.Length(min=2, max=25, message=u"Username too short"),
                                        validators.InputRequired(u"Forgot to input")])
    password = PasswordField("Password", [validators.Length(min=8, max=25, message=u"Password too short"),
                                            validators.InputRequired(u"Forgot to input")])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")

class RegisterForm(Form):
    username = StringField("Username", [validators.Length(min=2, max=25, message=u"Username too short"),
                                        validators.InputRequired(u"Forgot to input")])
    password = PasswordField("Password", [validators.Length(min=8, max=25, message=u"Password too short"),
                                            validators.InputRequired(u"Forgot to input")])

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

class User(UserMixin):
    def __init__(self, id, username, token):
        self.id = id
        self.username = username
        self.token = token 

@login_manager.user_loader
def load_user(user_id):
    app.logger.debug("LOAD USER: " + str(session['id']) + " " + session['username'] + session['token'])
    username = session['username'] 
    if username == None:
        return None
    user = User(int(user_id), username, session.get('token')) 
    return user


###
# Pages
###

@app.route("/")
@app.route("/index")
@login_required
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        remember = request.form.get("remember", "false") == "true"
        h = hashlib.new('sha512_256')
        h.update(request.form["password"].encode('utf-8'))
        h_passwd = h.hexdigest()
        app.logger.debug("WEB LOGIN HPASS: " + h_passwd)
        r = requests.get("http://"+API_ADDR+":"+API_PORT+"/token?username="+username+"&password="+h_passwd)
        if r.status_code == 200:
            resp = json.loads(r.text)
            token = resp.get('token')
            user = User(int(resp['id']), username, token)
            if login_user(user, remember=remember):
                app.logger.debug("AUTH: " + str(current_user.is_authenticated))
                session['username'] = username
                session['token'] = token
                session['id'] = int(resp['id']) 
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash("The username or password you entered is wrong")
    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    app.logger.debug("CREATE FORM")
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        app.logger.debug("IN MAIN IF")
        username = request.form["username"]
        app.logger.debug("GOT USERNAME: " + username)
        entry = auth_db.users.find_one({'username': username})
        if entry == None:
            app.logger.debug("NO CURRENT USER")
            remember = request.form.get("remember", "false") == "true"
            h = hashlib.new('sha512_256')
            h.update(request.form["password"].encode('utf-8'))
            h_passwd = h.hexdigest()

            app.logger.debug("WEB REG HPASS: " + h_passwd)
            app.logger.debug("GOT PASSWD: "+h_passwd)
            r = requests.get("http://"+API_ADDR+":"+API_PORT+"/register?username="+username+"&password="+h_passwd)
            if r.status_code != 200:
                app.logger.debug("FAILED TO REG: " + r.text)
                flash("Failed to register")
            else:
                app.logger.debug("REGISTERED SUCCESS")
                flash("Registration successful")
        else:
            app.logger.debug("USER EXISTS")
            flash("The username you entered already exists")
    else:
        flash("Invalid input")
    app.logger.debug("RE RENDER")
    return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############


#Simply performs a few different types of API data GETs to display on the page
@app.route("/_get_api_data")
def _calc_times():
    token = session.get("token")
    if token == None:
        token = ""

    app.logger.debug("AJAX TOKEN: " + token)
    r = requests.get("http://"+API_ADDR+":"+API_PORT+"/listAll?top=3&token=" + token)
    all_text = r.text

    r = requests.get("http://"+API_ADDR+":"+API_PORT+"/listOpenOnly/csv?top=3&token=" + token)
    open_text = r.text

    r = requests.get("http://"+API_ADDR+":"+API_PORT+"/listCloseOnly/csv?top=3&token=" + token)
    close_text = r.text

    return flask.jsonify({"all": all_text, "open": open_text, "close": close_text})


app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
