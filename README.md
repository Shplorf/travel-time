# travel-time
This script leverages the Google distance matrix API to find commute times to different office locations for a group of people
## Required Python modules:
- pytz (for time zone stuff)
- requests (for API requests)

## Usage
```
usage: travel_times.py [-h] [-d DAY_OF_WEEK] [-i INPUT_FILE] [-o OUTPUT_FILE]
                       api_key address

Travel times calculator

positional arguments:
  api_key               Google Distance Matrix API key
  address               Destination address

optional arguments:
  -h, --help            show this help message and exit
  -d DAY_OF_WEEK, --day_of_week DAY_OF_WEEK
                        Day of week to calculate travel times for. 0 = Monday,
                        1=Tuesday, 2=Wednesday... (default: 0)
  -i INPUT_FILE, --input_file INPUT_FILE
                        CSV File with addresses and preferred travel modes
                        (default: input.csv)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        CSV File duplicating input data, but also adding
                        travel times (default: travel_times.csv)

```

# Input
No header

Field order: name, address, mode of transportation

Example row: `John Doe,123 Some St Cambridge MA,driving`

Valid modes:
- driving
- walking
- bicycling
- transit

# Output
CSV header: `name,address,mode,driving_6_3,driving_7_4,driving_8_5,driving_9_6,driving_10_7,driving_11_8,bicycling_6_3,bicycling_7_4,bicycling_8_5,bicycling_9_6,bicycling_10_7,bicycling_11_8,transit_6_3,transit_7_4,transit_8_5,transit_9_6,transit_10_7,transit_11_8,walking_6_3,walking_7_4,walking_8_5,walking_9_6,walking_10_7,walking_11_8`

Columns after mode represent permutations of the modes of transport with work day intervals, from departure from home to departure from work. Values are total commute time (in + out) in seconds

Example row: `John Doe,123 Some St Cambridge MA,Transit,1354,1353,1358,1379,1398,1451,2515,2515,2515,2515,2515,2515,5964,5911,5911,4693,5046,5175,7015,7015,7015,7015,7015,7015`
