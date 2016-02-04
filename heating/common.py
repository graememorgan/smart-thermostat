import datetime

def epoch(date):
  return (date - datetime.datetime(1970, 1, 1)).total_seconds()

