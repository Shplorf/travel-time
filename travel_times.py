import argparse
import csv
import json
import datetime

import pytz
import requests


# Constants
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

MODES = [
    'driving',
    'bicycling',
    'transit',
    'walking'
]

TZ = pytz.timezone('America/New_York')

API_ENDPOINT_STR = 'https://maps.googleapis.com/maps/api/distancematrix/json'

# End Constants


# Utility functions

def next_weekday(d, weekday):
    """
    Returns the date of the next [weekday] after date [d]
    :param d: datetime object
    :param weekday: integer between 0 and 6, where 0 = Monday, 1 = Tuesday, etc...
    :return: datetime object of the next [weekday] after date [d]
    """

    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def get_times(day_of_week, times):
    """
    Given a list of time slot interval dicts, return a dict of tuples where the keys are the names of the time slots
    and the two vlaues are datetime objects representing the corresponding start and end times on the next
    [day_of_week] day of the week after today.
    :param day_of_week: integer between 0 and 6, where 0 = Monday, 1 = Tuesday, etc...
    :param times: List of dicts in the following format:
        [{
            'name': '6_3',
            'start': 6,
            'end': 15
        }]
    :return: List of dicts in the following format:
        [{
            'name': '6_3',
            'start': datetime object,
            'end': datetime object
        }]
    """

    day = next_weekday(datetime.date.today(), day_of_week)
    out_times = []

    for time in times:
        out_times.append({
            'name': time['name'],
            'start': datetime.datetime.combine(day, datetime.time(hour=time['start'], tzinfo=TZ)),
            'end': datetime.datetime.combine(day, datetime.time(hour=time['end'], tzinfo=TZ))
        })

    return out_times


def add_travel_times(dst_address, direction, people, time_slots, api_key):
    """
    Given a destination address, direction, a lit of dicts representing people, a list of dicts representing time slots,
    and a Google distance matrix API key, populates the given people list of dicts with travel times for all
    modes of transportation in each of the given time slots.
    :param dst_address: String, address of commute destination
    :param direction: String, 'work' or 'home'
    :param people: list of dicts in the following format:
        {
            'name': 'John Doe',
            'address': '123 Some St Cambridge MA',
            'mode': 'transit'
        }
    :param time_slots: list of dicts in the following format:
        {
            'name': '9_6',
            'start': datetime object
            'end': datetime object
        }
    :param api_key: Google distance matrix API key
    """
    addresses = map(lambda x: x['address'], people)
    request_params = []

    if direction == 'work':
        time = 'start'
        origins = '|'.join(addresses)
        destinations = dst_address
    else:
        time = 'end'
        origins = dst_address
        destinations = '|'.join(addresses)

    for mode in MODES:
        for time_slot in time_slots:
            request_params.append({
                'mode': mode,
                'origins': origins,
                'destinations': destinations,
                'key': api_key,
                'departure_time': int(
                    (time_slot[time] - datetime.datetime(1970, 1, 1, tzinfo=TZ)).total_seconds())
            })

    i = 0
    for mode in MODES:
        if mode == 'driving':
            dur_str = 'duration_in_traffic'
        else:
            dur_str = 'duration'
        j = 0
        for time_slot in time_slots:

            result = requests.get(API_ENDPOINT_STR, params=request_params.pop(0))

            if result.status_code == 200:
                body = json.loads(result.text)

                for k in xrange(len(addresses)):
                    person = people[k]
                    person.setdefault('times', {})
                    person['times'].setdefault(time_slot['name'], {})
                    person['times'][time_slot['name']].setdefault(mode, 0)

                    if direction == 'work':
                        row_index = k
                        element_index = 0
                    else:
                        row_index = 0
                        element_index = k

                    element = body['rows'][row_index]['elements'][element_index]

                    if element['status'] != 'OK':
                        person['times'][time_slot['name']][mode] = element['status']
                    elif type(person['times'][time_slot['name']][mode]) is int:
                        person['times'][time_slot['name']][mode] += element[dur_str]['value']
            else:
                raise ValueError("Non-200 status code! URL:%s" % result.url)
            j += 1
        i += 1


def write_results(people, file_name):
    """
    Given a list of dicts with information about people and their travel times, write that info to a CSV file
    :param people: list of people dicts
    :param file_name: String, output file path
    """

    with open(file_name, 'w') as csv_out:

        out_fields = []
        time_slot_names = map(lambda x: x['name'], time_slots)
        for mode in MODES:
            for time_slot_name in time_slot_names:
                out_fields.append(mode + '_' + time_slot_name)

        writer = csv.DictWriter(
            csv_out,
            fieldnames=IN_HEADER + out_fields
        )
        writer.writeheader()

        for i in xrange(len(people)):

            person = people[i]
            for mode in MODES:
                for time_slot_name in time_slot_names:
                    person[mode + '_' + time_slot_name] = person['times'][time_slot_name][mode]

            del person['times']

        writer.writerows(people)
# End utility functions


# Command line arg parsing
parser = argparse.ArgumentParser(
    description='Travel times calculator',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    'api_key',
    help='Google Distance Matrix API key',
    type=str
)

parser.add_argument(
    'address',
    help='Destination address',
    type=str
)

parser.add_argument(
    '-d',
    '--day_of_week',
    help='Day of week to calculate travel times for. 0 = Monday, 1=Tuesday, 2=Wednesday...',
    type=int,
    default=0
)

parser.add_argument(
    '-i',
    '--input_file',
    help='CSV File with addresses and preferred travel modes',
    type=str,
    default='input.csv'
)

parser.add_argument(
    '-o',
    '--output_file',
    help='CSV File duplicating input data, but also adding travel times',
    type=str,
    default='travel_times.csv'
)

# End command line arg parsing


# Main body of script

args = parser.parse_args()
time_slots = get_times(args.day_of_week, WORK_HOURS)

with open(args.input_file, 'r') as csv_in:

    # Read in CSV
    reader = csv.DictReader(csv_in, fieldnames=IN_HEADER)
    ppl = []
    for row in reader:
        ppl.append(row)

    # For each direction, mode and time slot, ask the Google API for the travel times
    for direction in ['work', 'home']:
        add_travel_times(
            dst_address=args.address,
            direction=direction,
            people=ppl,
            time_slots=time_slots,
            api_key=args.api_key
        )

    # Output results to CSV
    write_results(
        people=ppl,
        file_name=args.output_file
    )

# End main body of script
