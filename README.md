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

#### crontab.weather_dl.txt installation as a cronjob

To add a cronjob that downloads the weather observations, as outlined above, edit the crontab with
```
crontab -e
```
Then copy the contents into the crontab, with your editor. Substitute `<PATH_TO>/bomreader` in the PATH with the location of the bomreader installation, and change `cd $HOME/bomdata` to specify the location where data is to be downloaded to, save and exit.

To verify that the cronjob has been installed correctly, issue the command
```
crontab -l
```


