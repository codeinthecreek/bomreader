# bomreader
BoM Reader is used to process JSON files of Australian weather observations obtained from the [Bureau of Meteorology](http://www.bom.gov.au) and present the results as typical conditions for times of day, for each day and overall, over the data's timespan.

All code is currently only Linux terminal-based. The main program is written in Python 3 with an Sqlite3 backend. All other code is written in Bash Shell (GNU version >= 4). `readweatherobs.sh` uses `jq`, a command line JSON processor, to do its work. All code was tested under Arch Linux.


## Files

### Observation Data Processing
* bomreader.py - The main program to be used for reading, processing and displaying BoM observations.
* readweatherobs.sh - Provides basic functionality, reading and presenting observation data.

### Supplementary Scripts
* getweatherobs.sh - Downloads the latest observation data for the specified location.
* getallobs.sh - Download observations for all sites of interest. Used in crontab.
* crontab.weather_dl.txt - Example crontab for downloading observation data every odd day of month.

## Usage

Note that your `$PATH` environment variable should be updated to point to the installed location of the following scripts and python code, otherwise to run these they will need to be prefixed with `./` if running from the installed location, or the path. The examples given below assume that the PATH has been set.

### Downloading the data
The first step is to download some observation data from BoM. The `getweatherobs.sh` script can be used for this, however, it currently only knows the product codes of a handful of locations along the Queensland coast between Brisbane and Cooktown, plus Darwin, in the Northern Territory. This needs to be expanded and improved upon.

The `getallobs.sh` script downloads observations for all (currently) supported locations (as more locations are supported by `getweatherobs.sh`, this may cease to be the case. It is used by the example crontab (see following), and can be modified to suit locations of interest.

The example crontab, `crontab.weather_dl.txt` can be used to download data for all locations of interest, every second (odd) calendar day. This frequency was chosen as observation files contain 72 hours of data, so there is little chance of missing data. Additionally, the download time was chosen to be 22:15 (10:15 PM), so as to complete one of the daily time periods ("evening" from 6 PM to 10 PM). See section on `bomreader.py` for more information regarding periods.

#### getweatherobs.sh example usage

To get a list of supported locations:
```
getweatherobs.sh
```

To download the latest (72 hours of) observation data from the Mt Stuart station, Townsville:
```
getweatherobs.sh Townsville_MS
```

#### getallobs.sh usage

This is run without arguments, as:
```
getallweatherobs.sh
```

#### Automating observation data download with a cronjob using the crontab.weather_dl.txt template

To add a cronjob that downloads the weather observations, as outlined above, edit the crontab with
```
crontab -e
```
Then copy the contents into the crontab, with your editor. Substitute `<PATH_TO>/bomreader` in the PATH with the location of the bomreader installation, and change `cd $HOME/bomdata` to specify the location where data is to be downloaded to, save and exit.

To verify that the cronjob has been installed correctly, issue the command
```
crontab -l
```

### Processing Observations

#### Reading the JSON observation data with readweatherobs.sh

`readweatherobs.sh` provides basic functionality for reading the JSON-based observation data.

The usage, as given when no arguments are supplied is:
```
Usage: readweatherobs.sh [field-options] [filename]
Field options available: tahdwrcp
The default options, if not otherwise specified, are `-ta`.
    -t: air_temp; -a: apparent_t; -h: rel_hum; -d: dewpt;
    -w: wind_dir wind_spd_kmh; -r: rain_trace; -c: cloud; -p: press_msl
if filename isn't supplied then standard input is assumed
```

An example of usage:
```
readweatherobs.sh -athr Townsville_MS-2018-03-01.json
```
Provides output in reverse chronological order containing lines like:
```
Mount Stuart (Defence) 27/02:30pm : 24.1 feels like 27.6 humidity: 93 rain: 31.4
Mount Stuart (Defence) 27/02:00pm : 24.6 feels like 25.3 humidity: 98 rain: 18.8
Mount Stuart (Defence) 27/01:30pm : 29.5 feels like 33.6 humidity: 72 rain: 0.2
Mount Stuart (Defence) 27/01:00pm : 31.5 feels like 36.8 humidity: 66 rain: 0.2
Mount Stuart (Defence) 27/12:30pm : 31.5 feels like 37.1 humidity: 68 rain: 0.2
Mount Stuart (Defence) 27/12:00pm : 30.4 feels like 34.6 humidity: 69 rain: 0.2
```

#### Processing weather observations with bomreader.py

`bomreader.py` is the main program for processing and presenting BoM weather observation data, stored in json files. It takes one or more json files, calculates and outputs the typical temperatures & range, relative humidity (& cloudiness) for each (and summarised for the entire date range) night, morning, day and evening over the time period contained in the provided data. This gives a more accurate reflection of weather & climate (for comparison), as opposed to just maximum and minimum temperatures.

Note that the periods of the day are defined as
* night: 10 PM - 6 AM
* morning: 6 AM - 10 AM
* daytime: 10 AM - 6 PM
* evening: 6 PM - 10 PM

such that the times of rapidly rising and falling temperatures (morning, evening) are separated from times of more stable temperatures (night, daytime), and time periods correspond roughly with perceptions of these times of day.

The usage for `bomreader.py` is:
```
bomreader.py [-h] [-d] [-s] jsonfile1 [jsonfile 2 ...]
```
where the '-h' option provides a brief usage and help message, '-d' is for debugging, and '-s' provides the summary only.

Hence, `bomreader.py` can be run simply as, for example:
```
bomreader.py Townsville_MS-2018-03-01.json
```
Which provides the following output:
```
2018-02-27 overnight: Mount Stuart (Defence) 24.1 +/-0.2 (d=0.0) 100%
2018-02-27 morning: Mount Stuart (Defence) 25.1 +/-2.4 (d=0.0) 94%
2018-02-27 daytime: Mount Stuart (Defence) 27.4 +/-3.7 (d=0.0) 82%
2018-02-27 evening: Mount Stuart (Defence) 25.7 +/-0.4 (d=0.0) 94%
2018-02-28 overnight: Mount Stuart (Defence) 23.7 +/-0.9 (d=-0.4) 100%
2018-02-28 morning: Mount Stuart (Defence) 23.5 +/-0.1 (d=-1.7) 100%
2018-02-28 daytime: Mount Stuart (Defence) 24.4 +/-1.1 (d=-3.1) 98%
2018-02-28 evening: Mount Stuart (Defence) 23.8 +/-0.4 (d=-1.9) 99%
2018-03-01 overnight: Mount Stuart (Defence) 24.1 +/-0.4 (d=0.4) 100%
2018-03-01 morning: Mount Stuart (Defence) 23.9 +/-0.3 (d=0.5) 100%
2018-03-01 daytime: Mount Stuart (Defence) 25.4 +/-1.2 (d=1.0) 95%
2018-03-01 evening: Mount Stuart (Defence) 25.5 +/-0.2 (d=1.7) 95%
Observations cover 3 days, from 2018-02-26 to 2018-03-01
Mount Stuart (Defence): overnight 23.9 +/-0.5 [range 23.7 - 24.1; interday +/-0.4] @ 100%
Mount Stuart (Defence): morning 24.2 +/-0.9 [range 23.5 - 25.1; interday +/-1.1] @ 98%
Mount Stuart (Defence): daytime 25.7 +/-2.0 [range 24.4 - 27.4; interday +/-2.1] @ 91%
Mount Stuart (Defence): evening 25.0 +/-0.3 [range 23.8 - 25.7; interday +/-1.8] @ 96%
```
showing: date, period, location, temperature +/- range, inter-day difference, and relative humidity.


## TODO

Currently `bomreader.py` just processes temperature and relative humidity (apparent temperature is recorded but not yet processed, and cloud oktas, while processed is not output). In future, rainfall readings, wind direction and speed should also be recorded and processed.

`getweatherobs.sh` needs a better way of obtaining product codes for stations (currently hard coded), and needs to be extended to other states and territories.

