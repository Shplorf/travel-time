import argparse
import csv
import json
import datetime

import pytz
import grequests

WORK_HOURS = [
    {
        'name': '6_3',
        'start': 6,
        'end': 15
    },
    {
        'name': '7_4',
        'start': 7,
        'end': 16
    },
    {
        'name': '8_5',
        'start': 8,
        'end': 17
    },
    {
        'name': '9_6',
        'start': 9,
        'end': 18
    },
    {
        'name': '10_7',
        'start': 10,
        'end': 19
    },
    {
        'name': '11_8',
        'start': 11,
        'end': 20
    }
]

IN_HEADER = [
    'name',
    'address',
    'mode'
]

MODES = ['driving', 'bicycling', 'transit', 'walking']

TZ = pytz.timezone('America/New_York')

API_ENDPOINT_STR = 'https://maps.googleapis.com/maps/api/distancematrix/json'

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
    help='Google Distance Matrix API key',
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

parser.add_argument(
    '-m',
    '--mode',
    help='Mode of transportation',
    type=str,
    default='preferred',
    choices=['preferred', 'driving', 'bicycling', 'transit', 'walking']
)


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_times(day_of_week, times):

    day = next_weekday(datetime.date.today(), day_of_week)
    out_times = {}

    for time in times:
        out_times[time['name']] = (
            datetime.datetime.combine(day, datetime.time(hour=time['start'], tzinfo=TZ)),
            datetime.datetime.combine(day, datetime.time(hour=time['end'], tzinfo=TZ))
        )

    return out_times

args = parser.parse_args()
time_slots = get_times(args.day_of_week, WORK_HOURS)

with open(args.input_file, 'r') as csv_in:

    reader = csv.DictReader(csv_in)

    people = []
    addresses = []
    modes = []

    # Reading in CSV
    for row in reader:
        people.append(row)
        addresses.append(row[IN_HEADER[1]])
        modes.append(row[IN_HEADER[2]])

    # For each mode and time slot, ask the Google API for the travel times

    # Home -> office
    #
    # Preparing requests and sending them out in parallel
    request_params = []
    for mode in MODES:
        for time_slot_name, time_slot in time_slots.iteritems():
            request_params.append({
                'mode': mode,
                'origins': '|'.join(addresses),
                'destinations': args.address,
                'key': args.api_key,
                'departure_time': int((time_slot[0] - datetime.datetime(1970,1,1, tzinfo=TZ)).total_seconds())
            })
    results = grequests.map(grequests.get(API_ENDPOINT_STR, params=p) for p in request_params)

    # Parsing results
    i = 0
    for mode in MODES:
        if mode == 'driving':
            dur_str = 'duration_in_traffic'
        else:
            dur_str = 'duration'
        j = 0
        for time_slot_name, time_slot in time_slots.iteritems():

            result = results[i + j]
            if result.status_code == 200:
                body = json.loads(result.text)

                for k in xrange(len(addresses)):
                    person = people[k]
                    person.setdefault('times', {})
                    person['times'].setdefault(time_slot_name, {})
                    person['times'][time_slot_name].setdefault(mode, 0)
                    person['times'][time_slot_name][mode] += body['rows'][k]['elements'][0][dur_str]['value']
            j += 1
        i += 1
    # End Home -> office

    # Office -> home
    #
    # Preparing requests and sending them out in parallel
    request_params = []
    for mode in MODES:
        for time_slot_name, time_slot in time_slots.iteritems():
            request_params.append({
                'mode': mode,
                'origins': args.address,
                'destinations': '|'.join(addresses),
                'key': args.api_key,
                'departure_time': int((time_slot[1] - datetime.datetime(1970, 1, 1, tzinfo=TZ)).total_seconds())
            })
    results = grequests.map(grequests.get(API_ENDPOINT_STR, params=p) for p in request_params)

    # Parsing results
    i = 0
    for mode in MODES:
        if mode == 'driving':
            dur_str = 'duration_in_traffic'
        else:
            dur_str = 'duration'
        j = 0
        for time_slot_name, time_slot in time_slots.iteritems():

            result = results[i + j]
            if result.status_code == 200:
                body = json.loads(result.text)

                for k in xrange(len(addresses)):
                    person = people[k]
                    person['times'][time_slot_name][mode] += body['rows'][0]['elements'][k][dur_str]['value']
            j += 1
        i += 1

    # Output results to CSV
    with open(args.output_file, 'w') as csv_out:

        writer = csv.DictWriter(
            csv_out,
            fieldnames=IN_HEADER + time_slots.keys()
        )
        writer.writeheader()

        # Sets mode of transportation of person p to mode m
        def set_mode(p, m):
            p['mode'] = m
            for slot_name in time_slots.keys():
                p[slot_name] = p['times'][slot_name][m]

        for i in xrange(len(people)):

            person = people[i]

            if args.mode == 'preferred':
                set_mode(person, modes[i])
            else:
                set_mode(person, args.mode)

            del person['times']

        writer.writerows(people)
