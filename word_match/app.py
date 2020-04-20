import os
from flask import Flask
from flask_socketio import SocketIO


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GAMEMASTER_CODE'] = os.environ['GAMEMASTER_CODE']
socketio = SocketIO(app)

games = {}
cardsets = {}
