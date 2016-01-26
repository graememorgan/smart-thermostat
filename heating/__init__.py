from flask import Flask

from heating.boiler import boiler
from heating.sensors import sensors

app = Flask(__name__)
app.config.from_object('heating.settings')

app.register_blueprint(boiler)
app.register_blueprint(sensors)

