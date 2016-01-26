from flask import Blueprint, Flask, Response, render_template, json, request
import datetime
from collections import defaultdict
from database import *
from heating.auth import requires_auth

sensors = Blueprint("sensors", __name__, template_folder="templates")

def currentValues():
  nested_dict = lambda: defaultdict(nested_dict)
  current = nested_dict()

  maxima = (Measurement
    .select(Measurement.location, Measurement.quantity, fn.MAX(Measurement.time).alias("max_time"))
    .join(Location)
    .switch(Measurement)
    .join(Quantity)
    .group_by(Quantity.id, Location.id)
    .alias("measurement_max_subquery"))

  q = (Measurement
    .select(Measurement.location, Measurement.quantity, Measurement.value)
    .join(Location)
    .switch(Measurement)
    .join(Quantity)
    .join(
      maxima,
      on=(
        (Measurement.location == maxima.c.location_id) &
        (Measurement.quantity == maxima.c.quantity_id) &
        (Measurement.time == maxima.c.max_time)
      ))
    .where(Location.show))

  for m in q:
    if m.quantity.name == "temperature":
      current[m.location.name][m.quantity.name] = "%.1f" % (m.value)
    else:
      current[m.location.name][m.quantity.name] = "%d" % (m.value)

  return current

@sensors.route("/")
@requires_auth
def index():
  current = currentValues()
  return render_template("index.htm", current=current)

@sensors.route("/current")
@requires_auth
def current():
  current = currentValues()
  return json.dumps(current)

@sensors.route("/<location>/chart", defaults={"date": None})
@sensors.route("/<location>/chart/<date>")
def locationChart(location, date):
  if date is None:
    date = datetime.datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
  else:
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

  prevDate = (date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
  nextDate = (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

  data = {"temperature": [], "RH": []}
  q = (Measurement
    .select()
    .join(Quantity)
    .switch(Measurement)
    .join(Location)
    .where(
      ((Quantity.name == "temperature") | (Quantity.name == "RH"))
      & (Location.name == location)
      & (Measurement.time >= date)
      & (Measurement.time < date + datetime.timedelta(days=1))
    )
    .order_by(Measurement.time))
  for m in q:
    data[m.quantity.name].append([(m.time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000, m.value])
  
  data = {key: json.dumps(value) for key, value in data.iteritems()}
  return render_template("location_chart.htm", data=data, location=location, prevDate=prevDate, nextDate=nextDate)

@sensors.route("/chart")
def chart():
  traces = {}
  for m in Measurement.select(Measurement.location, Measurement.quantity).distinct().join(Quantity).switch(Measurement).join(Location):
    if m.location.name not in traces:
      traces[m.location.name] = []
    traces[m.location.name].append(m.quantity.name)
  print traces
  return render_template("chart.htm", traces=traces)

@sensors.route("/data/<location>/<quantity>")
def chartData(location, quantity):
  output = []
  for m in Measurement.select().join(Quantity).switch(Measurement).join(Location).where((Quantity.name == quantity) & (Location.name == location)).order_by(Measurement.time):
    output.append([(m.time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000, m.value])
  return json.dumps(output)


