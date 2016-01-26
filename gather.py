#!/usr/bin/python

from peewee import *
import requests
from heating.database import *

for location in Location.select():
	if location.hostname:
		print("Working on %s" % (location.name))
		r = requests.get('http://%s/raw' % (location.hostname))
		if r.text:
			for quantity, sensor, value in [line.split("\t") for line in r.text.split("\n") if line]:
				if quantity == "temperature" and sensor == "bmp180":
					continue
				m = Measurement(
					location=location,
					value=float(value),
					quantity=Quantity.get_or_create(name=quantity)[0],
					sensor=Sensor.get_or_create(name=sensor)[0])
				m.save()
				print quantity, sensor, value

