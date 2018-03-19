# bomreader
BoM Reader is used to process JSON files of Australian weather observations obtained from the [Bureau of Meteorology](http://www.bom.gov.au) and present the results as typical conditions for times of day, for each day and overall, over the data's timespan.

All code is currently only Linux terminal-based. The main program is written in Python 3 with an Sqlite3 backend. All other code is written in Bash Shell (GNU version >= 4). The code was tested under Arch Linux.

## Files

### Observation Data Processing
* bomreader.py - The main program to be used for reading, processing and displaying BoM observations.
* readweatherobs.sh - Provides basic functionality, reading and presenting observation data.

### Supplementary Scripts
* getweatherobs.sh - Downloads the latest observation data for the specified location.
* getallobs.sh - Download observations for all sites of interest. Used in crontab.
* crontab.weather_dl.txt - Example crontab for downloading observation data every odd day of month.

