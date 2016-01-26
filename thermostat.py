#!/usr/bin/python

import datetime, requests, time, os
from collections import defaultdict
from heating.database import *
import logging
from apscheduler.scheduler import Scheduler

logging.basicConfig()

cron = Scheduler(standalonek=True)
# Explicitly kick off the background thread
cron.start()

def getTemperature():
  r = requests.get('http://probe1/raw')
  if r.text:
    for quantity, sensor, value in [line.split("\t") for line in r.text.split("\n") if line]:
      if quantity == "temperature" and sensor != "bmp180":
        return float(value)
  return 0.0

def boiler(state):
  r = requests.get('http://433mhz/boiler?state=%s' % (["off", "on"][state],), timeout=10)
  if state:
    print str(datetime.datetime.now()), "boiler on"
  else:
    print str(datetime.datetime.now()), "boiler off"

state = False

@cron.interval_schedule(minutes=1)
def job_function():
  global state
  # select the current setpoint temperature
  now = datetime.datetime.now().time()

  occupied = Person.select().join(State).where(State.name == "connected").count()
  temperature = getTemperature()
  goal = None
  forced = False

  # check for a current setpoint
  try:
    setpoint = Setpoint.get((Setpoint.start < now) & (Setpoint.end > now) & (Setpoint.weekday == datetime.datetime.now().weekday()))
    goal = setpoint.setpoint
    forced = setpoint.forced
  except DoesNotExist:
    pass

  # check for a current forced temperature
  try:
    nowdate = datetime.datetime.now()
    override = BoilerOverride.get((BoilerOverride.start < nowdate) & (BoilerOverride.end > nowdate))
    goal = override.setpoint
    forced = True
  except DoesNotExist:
    pass
  

  if goal is not None:
    error = goal - temperature
    if forced or occupied:
      if error > 0.2:
        state = True
      if error < 0:
        state = False
    else:
      state = False
  else:
    state = False
  
  print("%s: T = %f, goal = %f, state = %d" % (str(now), temperature, goal, state))

  BoilerLog(
    setpoint=goal,
    temperature=temperature,
    boiler=state).save()

  boiler(state)

while True:
  time.sleep(10)

