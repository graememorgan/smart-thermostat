#!/usr/bin/python

import datetime
from peewee import *
from settings import *

db = MySQLDatabase(DB_DATABASE, user=DB_USERNAME, passwd=DB_PASSWORD)
db.get_conn().ping(True)

class BaseModel(Model):
  class Meta:
    database = db

class Location(BaseModel):
  name = CharField(unique=True, index=True)
  hostname = CharField()
  show = BooleanField(index=True)

class Quantity(BaseModel):
  name = CharField(unique=True, index=True)

class Sensor(BaseModel):
  name = CharField(unique=True, index=True)

class Measurement(BaseModel):
  location = ForeignKeyField(Location)
  quantity = ForeignKeyField(Quantity)
  sensor = ForeignKeyField(Sensor)
  time = DateTimeField(default=datetime.datetime.now)
  value = FloatField()

class State(BaseModel):
  name = CharField(unique=True, index=True)

class Person(BaseModel):
  name = CharField(unique=True, index=True)
  mac = CharField(index=True)
  state = ForeignKeyField(State)

class PersonEvent(BaseModel):
  person = ForeignKeyField(Person)
  state = ForeignKeyField(State)
  time = DateTimeField(default=datetime.datetime.now, index=True)

class Setpoint(BaseModel):
  weekday = IntegerField()
  start = TimeField(formats=["%H:%M"])
  end = TimeField(formats=["%H:%M"])
  setpoint = FloatField()
  forced = BooleanField()

class BoilerLog(BaseModel):
  time = DateTimeField(default=datetime.datetime.now, index=True)
  setpoint = FloatField()
  temperature = FloatField()
  boiler = BooleanField()

class BoilerOverride(BaseModel):
  start = DateTimeField(default=datetime.datetime.now, index=True)
  end = DateTimeField(default=datetime.datetime.now, index=True)
  setpoint = FloatField()

if __name__ == "__main__":
  db.create_tables([BoilerOverride])
