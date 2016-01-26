from flask import Blueprint, render_template, json, request
from heating.auth import requires_auth
from database import *

boiler = Blueprint("boiler", __name__, template_folder="templates")

@boiler.route("/schedule")
@requires_auth
def schedule():
  data = []
  for i in range(7):
    data.append([[],[]])
  for setpoint in Setpoint.select().order_by(Setpoint.start):
    weekday = (setpoint.weekday + 1) % 7
    data[weekday][1].append([setpoint.setpoint, setpoint.forced])
    if setpoint.start:
      data[weekday][0].append(float(setpoint.start.seconds) / 3600)
  return render_template("schedule.htm", data=json.dumps(data))

@boiler.route("/schedule/save", methods=["POST"])
@requires_auth
def scheduleSave():
  data = json.loads(request.form["data"])
  Setpoint.delete().execute()
  for i, day in enumerate(data):
    weekday = (i + 6) % 7 # convert JavaScript day to Python
    positions = [datetime.time(hour=0, minute=0)] + [datetime.time(hour=int(h), minute=int(60 * (h % 1))) for h in day[0]] + [datetime.time(hour=23, minute=59)]
    temperatures = [float(t) for t, f in day[1]]
    forced = [f for t, f in day[1]]

    for i in range(len(temperatures)):
      s = Setpoint(
        weekday=weekday,
        setpoint=temperatures[i],
        start=positions[i],
        end=positions[i + 1],
        forced = forced[i])
      s.save()
  return ""

@boiler.route("/boiler/state")
@requires_auth
def boilerState():
  """Returns 1 if the boiler is currently on, 0 if currently off"""
  try:
    log = BoilerLog.select().order_by(BoilerLog.time.desc()).get() 
    return str(1 if log.boiler else 0)
  except DoesNotExist:
    return "0"

@boiler.route("/boiler/setpoint", methods=["GET"])
@requires_auth
def boilerOverride():
  """returns any current override on the setpoint temperature.
  format: [boolean: override present, float: temperature, int: remaining seconds]
  """
  try:
    now = datetime.datetime.now()
    override = BoilerOverride.get((BoilerOverride.start <= now) & (BoilerOverride.end > now))
    return json.dumps([True, override.setpoint, (override.end - now).total_seconds()])
  except DoesNotExist:
    try:
      now = datetime.datetime.now().time()
      setpoint = Setpoint.get((Setpoint.start < now) & (Setpoint.end > now) & (Setpoint.weekday == datetime.datetime.now().weekday()))
      return json.dumps([False, setpoint.setpoint, 0])
    except DoesNotExist:
      return json.dumps([False, 0, 0])

@boiler.route("/boiler/override", methods=["POST"])
@requires_auth
def boilerOverrideSet():
  """Sets the current override for the boiler.  If a setpoint is not provided, the current override is removed."""
  # delete any current overrides
  now = datetime.datetime.now()
  BoilerOverride.delete().where((BoilerOverride.start <= now) & (BoilerOverride.end > now)).execute()

  # if no setpoint is specified, we just deleted existing ones, so auto mode is set
  if "setpoint" in request.form and "remaining" in request.form:
    BoilerOverride(
      setpoint=request.form["setpoint"],
      start=datetime.datetime.now(),
      end=datetime.datetime.now() + datetime.timedelta(minutes=int(request.form["remaining"]))
    ).save()

  return "0"

@boiler.route("/boiler/chart", defaults={"date": None})
@boiler.route("/boiler/chart/<date>")
def boilerChart(date):
  if date is None:
    date = datetime.datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
  else:
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

  prevDate = (date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
  nextDate = (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

  data = {"temperature": [], "setpoint": [], "state": []}
  q = (BoilerLog
    .select()
    .where(
      (BoilerLog.time >= date)
      & (BoilerLog.time < date + datetime.timedelta(days=1))
    )
    .order_by(BoilerLog.time))
  for h in q:
    time = (h.time - datetime.datetime(1970, 1, 1)).total_seconds() * 1000
    data["temperature"].append([time, h.temperature])
    data["setpoint"].append([time, h.setpoint if h.setpoint != 0 else None])
    data["state"].append([time, int(h.boiler)])
  
  data = {key: json.dumps(value) for key, value in data.iteritems()}
  return render_template("boiler_chart.htm", data=data, prevDate=prevDate, nextDate=nextDate)

@boiler.route("/boiler/stats")
@requires_auth
def boilerStats():
  # this query is ugly. it gives days as integers in the format YYMMDD, which then need to be parsed out
  q = (BoilerLog
    .select((fn.FLOOR(BoilerLog.time / 1000000)).alias("day"), fn.COUNT(BoilerLog.id).alias("num"))
    .where(BoilerLog.boiler == True)
    .group_by(fn.FLOOR(BoilerLog.time / 1000000)))

  days = []
  data = []

  for log in q:
    days.append(datetime.date(year=int(log.day / 10000), month=int((log.day / 100) % 100), day=int(log.day % 100)).strftime("%m/%d"))
    data.append(log.num)
  return render_template("boiler_stats.htm", days=json.dumps(days), data=json.dumps(data))

