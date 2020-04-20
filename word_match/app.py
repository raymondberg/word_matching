import os

from flask import Flask
from flask_session import Session
from flask_socketio import SocketIO
import redis


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GAMEMASTER_CODE'] = os.environ['GAMEMASTER_CODE']

print("Configuring REDIS as session store")
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ['SESSION_STORE'])

socketio = SocketIO(app)
sess = Session(app)
