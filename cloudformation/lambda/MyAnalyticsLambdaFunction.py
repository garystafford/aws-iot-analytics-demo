import datetime


def convert_time(t):
    return "{}{}".format(datetime.datetime.utcfromtimestamp(t).isoformat(), '+0000')


def lambda_handler(event, context):
    for e in event:
        e['temp'] = round(e['temp'], 2)
        e['humidity'] = round(e['humidity'], 2)
        e['co'] = round(e['co'], 4)
        e['lpg'] = round(e['lpg'], 4)
        e['smoke'] = round(e['smoke'], 4)
        # e['ts'] = convert_time(e['ts'])
    return event
