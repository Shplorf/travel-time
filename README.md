# travel-time
## Required Python modules:
- pytz
- requests
- frogress

## Usage
```
usage: travel_times.py [-h] -a ADDRESS [-f INPUT_FILE] [-o OUTPUT_FILE] -k
                       API_KEY [-d DAY_OF_WEEK]

Travel times calculator

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        Destination address (default: None)
  -f INPUT_FILE, --input_file INPUT_FILE
                        CSV File with addresses and preferred travel modes
                        (default: data.csv)
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        CSV File duplicating input data, but also adding
                        travel times (default: travel_times.csv)
  -k API_KEY, --api_key API_KEY
                        Google Directions API key (default: None)
  -d DAY_OF_WEEK, --day_of_week DAY_OF_WEEK
                        Day of week to calculate travel times for. 0 = Monday,
                        1=Tuesday, 2=Wednesday... (default: 0)
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
CSV header: `name,address,mode,6_2,7_3,8_4,9_5,10_6,11_7`

Columns after mode represent 8-hour work day intervals. Values are total commute time (in + out) in seconds

Example row: `John Doe,123 Some St Cambridge MA,driving,1968,1968,1968,1968,1968,1968`