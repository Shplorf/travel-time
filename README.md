# travel-time
## Required Python modules:
- pytz (for time zone stuff)
- grequests (for easy parallel API requests)

## Usage
```
usage: travel_times.py [-h] [-m {preferred,driving,bicycling,transit,walking}]
                       [-d DAY_OF_WEEK] [-f INPUT_FILE] [-o OUTPUT_FILE]
                       api_key address

Travel times calculator

positional arguments:
  api_key               Google Distance Matrix API key
  address               Destination address

optional arguments:
  -h, --help            show this help message and exit
  -m {preferred,driving,bicycling,transit,walking}, --mode {preferred,driving,bicycling,transit,walking}
                        Mode of transportation (default: preferred)
  -d DAY_OF_WEEK, --day_of_week DAY_OF_WEEK
                        Day of week to calculate travel times for. 0 = Monday,
                        1=Tuesday, 2=Wednesday... (default: 0)
  -f INPUT_FILE, --input_file INPUT_FILE
                        CSV File with addresses and preferred travel modes
                        (default: data.csv)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        CSV File duplicating input data, but also adding
                        travel times (default: travel_times.csv)
```

# Input
CSV header: name,address,mode

Example row: `John Doe,123 Some St Cambridge MA,driving`

Valid modes:
- driving
- walking
- bicycling
- transit

# Output
CSV header: `name,address,mode,6_3,7_4,8_5,9_6,10_7,11_8`

Columns after mode represent work day intervals, from departure from home to departure from work. Values are total commute time (in + out) in seconds

Example row: `John Doe,123 Some St Cambridge MA,driving,1968,1968,1968,1968,1968,1968`
