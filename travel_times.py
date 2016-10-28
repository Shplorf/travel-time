import argparse
import csv
import json
import datetime

import pytz
import requests
import frogress

WORK_HOURS = {
    '6_2': (6, 14),
    '7_3': (7, 15),
    '8_4': (8, 16),
    '9_5': (9, 17),
    '10_6': (10, 18),
    '11_7': (11, 19)
}

IN_HEADER = {
    'name': 'name',
    'address': 'address',
    'mode': 'mode'
}

TZ = pytz.timezone('America/New_York')

parser = argparse.ArgumentParser(
    description='Travel times calculator',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    '-a',
    '--address',
    help='Destination address',
    type=str,
    required=True
)

parser.add_argument(
    '-f',
    '--input_file',
    help='CSV File with addresses and preferred travel modes',
    type=str,
    default='data.csv'
)

parser.add_argument(
    '-o',
    '--output_file',
    help='CSV File duplicating input data, but also adding travel times',
    type=str,
    default='travel_times.csv'
)

parser.add_argument(
    '-k',
    '--api_key',
    help='Google Directions API key',
    type=str,
    required=True
)

parser.add_argument(
    '-d',
    '--day_of_week',
    help='Day of week to calculate travel times for. 0 = Monday, 1=Tuesday, 2=Wednesday...',
    type=int,
    default=0
)


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_times(day_of_week, times):

    day = next_weekday(datetime.date.today(), day_of_week)
    out_times = {}

    for name, time_slot in times.iteritems():
        out_times[name] = (
            datetime.datetime.combine(day, datetime.time(hour=time_slot[0], tzinfo=TZ)),
            datetime.datetime.combine(day, datetime.time(hour=time_slot[1], tzinfo=TZ))
        )

    return out_times


args = parser.parse_args()
time_slots = get_times(args.day_of_week, WORK_HOURS)

with open(args.input_file, 'r') as csv_in, open(args.output_file, 'w') as csv_out:

    reader = csv.DictReader(csv_in)
    writer = csv.DictWriter(csv_out, fieldnames=['name', 'address', 'mode', '6_2', '7_3', '8_4', '9_5', '10_6', '11_7'])
    writer.writeheader()

    for row in frogress.bar(reader):

        output = row

        for time_slot_name, time_slot in time_slots.iteritems():

            total_time = 0

            for direction in [(0, 'arrival_time'), (1, 'departure_time')]:
                params = {
                    'mode': row[IN_HEADER['mode']],
                    'origin': row[IN_HEADER['address']],
                    'destination': args.address,
                    'key': args.api_key,
                    direction[1]: int(
                        (
                            time_slot[direction[0]] -
                            datetime.datetime(1970,1,1, tzinfo=TZ)
                        ).total_seconds()
                    )
                }
                r = requests.get('https://maps.googleapis.com/maps/api/directions/json', params=params)

                if r.status_code == 200:
                    body = json.loads(r.text)
                    total_time += body['routes'][0]['legs'][0]['duration']['value']

            output[time_slot_name] = total_time

        writer.writerow(output)