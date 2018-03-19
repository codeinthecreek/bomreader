#!/usr/bin/env python

"""
bomreader.py: process and present BoM weather observation data as typical
    temperature & humidity for periods of day, for each location, day
    and summarised for entire date range.

Usage: bomreader.py [-h] [-d] jsonfile1 [jsonfile 2 ...]

Description:
    bomreader.py is used to process JSON files of weather observations
    (each file is for a single location and covers up to 72 hours of data)
    obtained from BoM (http://www.bom.gov.au).
    The provided data is used to calculate the typical temperatures & range,
    relative humidity (& cloudiness) for night, morning, day and evening
    over the time period contained in the provided data.
    This gives a more accurate reflection of weather & climate (for comparison),
    as opposed to just maximum and minimum temperatures.

Author: Justin Lee, July 2017.
"""


import sys
import getopt
import logging
import json
import sqlite3
import textwrap
import os
import tempfile
from datetime import datetime

# define parts of day intervals (morn, day, eve, night)
MORNING_HOUR_START="06:00"
MORNING_HOUR_END="10:00"
DAYTIME_HOUR_START="10:00"
DAYTIME_HOUR_END="18:00"
EVENING_HOUR_START="18:00"
EVENING_HOUR_END="22:00"
OVERNIGHT_HOUR_START="22:00"
OVERNIGHT_HOUR_END="06:00"


# build the desired set of queries for morn, day, eve, night intervals
# return a dictionary of strings (keys as per intervals listed above)
# arguments:
#     select_str will be like: AVG(air_temp)
#     locid will be like: 94287
#     extra_conditions will be like: AND cloud_oktas >= 0
#     group_by will be like: GROUP BY date
#     aggregate will be like: AVG(t_spread)
# note: an aggregate query will perform a query on the results of the
# main query, which will be within parentheses and named with AS, eg:
#     SELECT AVG(t_spread) FROM (SELECT (MAX(air_temp)-MIN(air_temp)) AS t_spread FROM observation WHERE location_id=94294 AND (time BETWEEN "10:00" AND "18:00") GROUP BY date)
def buildDailyIntervalQueries(select_str, locid, extra_conditions='', group_by='', aggregate=''):

    dstr = "buildDailyIntervalQueries(select_str={}, locid={}, extra_conditions={}, group_by={}, aggregate={})".format(select_str, locid, extra_conditions, group_by, aggregate)
    logging.debug(dstr)

    if len(aggregate) > 0:
        aggregate = 'SELECT ' + aggregate + ' FROM ('
        group_by = group_by + ')'

    # build the common query string template, time specific parts added later
    qtemplate = "{} SELECT {} FROM datenorm_observation WHERE location_id={} {} AND ({{}}) {}".format(aggregate, select_str, locid, extra_conditions, group_by)
    dstr = "buildDailyIntervalQueries() query template is: {}".format(qtemplate)
    logging.debug(dstr)

    # the time section of the query is specific to each interval
    mornstr = "time BETWEEN \"{}\" and \"{}\"".format(MORNING_HOUR_START, MORNING_HOUR_END)
    daystr = "time BETWEEN \"{}\" and \"{}\"".format(DAYTIME_HOUR_START, DAYTIME_HOUR_END)
    evestr = "time BETWEEN \"{}\" and \"{}\"".format(EVENING_HOUR_START, EVENING_HOUR_END)
    nightstr = "time BETWEEN \"{}\" and \"{}\" OR time BETWEEN \"{}\" and \"{}\"".format(OVERNIGHT_HOUR_START, "24:00:00", "00:00:00", OVERNIGHT_HOUR_END)

    # the resulting complete query strings
    qry_strs = {
            'morn': qtemplate.format(mornstr),
            'day': qtemplate.format(daystr),
            'eve': qtemplate.format(evestr),
            'night': qtemplate.format(nightstr)
    }
    dstr = "buildDailyIntervalQueries() built query strings:\n{}\n{}\n{}\n{}".format(qry_strs['morn'], qry_strs['day'], qry_strs['eve'], qry_strs['night'])
    logging.debug(dstr)

    return qry_strs


# AVG/MAX/MIN temps within the daily intervals, across all samples for loc
# returns a dict of temps, keys are night, morn, day, eve
def calcTypicalTemps(dbc, locid, fn):
    qryfn = "{}(air_temp)".format(fn) # fn is AVG, MIN or MAX
    qry_strs = buildDailyIntervalQueries(qryfn, locid)
    result = {}
    for qry in qry_strs:
        dbc.execute(qry_strs[qry])
        result[qry] = float(dbc.fetchone()[0])
    return result


# this is done slightly differently to the other calcTypical.. functions
# it uses the daytoday_avgt_diffs view, instead of directly accessing
# datenorm_observation, which it is derived from
def calcTypicalTempDiff(dbc, locname):

    qtemplate = "SELECT AVG(ABS(tdiff)) FROM daytoday_avgt_diffs WHERE name = '{}' AND tod = '{}'"
    # the resulting complete query strings
    qry_strs = {
            'morn': qtemplate.format(locname, '1-morn'),
            'day': qtemplate.format(locname, '2-day'),
            'eve': qtemplate.format(locname, '3-eve'),
            'night': qtemplate.format(locname, '0-night')
    }

    dstr = "calcTypicalTempDiff() built query strings:\n{}\n{}\n{}\n{}".format(qry_strs['morn'], qry_strs['day'], qry_strs['eve'], qry_strs['night'])
    logging.debug(dstr)

    result = {}
    for qry in qry_strs:
        dbc.execute(qry_strs[qry])
        result[qry] = float(dbc.fetchone()[0])
    return result


# determine average of the temperature spread within a daily interval for loc
# returns a dict of temp spreads, keys are night, morn, day, eve
def calcTypicalTempSpread(dbc, locid):
    qry_strs = buildDailyIntervalQueries('(MAX(air_temp)-MIN(air_temp)) as t_spread', locid, '', 'GROUP BY date', 'AVG(t_spread)')
    result = {}
    for qry in qry_strs:
        dbc.execute(qry_strs[qry])
        result[qry] = float(dbc.fetchone()[0])
    return result


# average humidity within daily intervals, across all samples for given loc
# returns a dict of humidity, keys are night, morn, day, eve
def calcTypicalHumidity(dbc, locid):
    qry_strs = buildDailyIntervalQueries('AVG(relative_humidity)', locid)
    result = {}
    for qry in qry_strs:
        dbc.execute(qry_strs[qry])
        result[qry] = float(dbc.fetchone()[0])
    return result


# determine typical cloudiness (0-8) within a daily interval for given loc
# returns a dict of cloud oktas, keys are night, morn, day, eve
def calcCloudiness(dbc, locid):
    #qry_strs = buildDailyIntervalQueries('COUNT(cloud)', locid, "AND cloud LIKE '%cloudy'")
    qry_strs = buildDailyIntervalQueries('AVG(cloud_oktas)', locid, 'AND cloud_oktas >= 0')
    result = {}
    for qry in qry_strs:
        dbc.execute(qry_strs[qry])
        cloudiness = dbc.fetchone()[0]
        if cloudiness is None:
            cloudiness = '-1'
        result[qry] = int(cloudiness)
    return result


# print the results obtained from calc*() queries for a given location
def printLocationSummary(locname, temps, tranges, spread, diffs, humidity, cloud):
    # Note: cloud oktas doesn't appear useful, to print, use for eg:
    #       print("{}/8".format(cloud['morn']))

    tod_strs = {
            'morn': 'morning',
            'day': 'daytime',
            'eve': 'evening',
            'night': 'overnight'
    }

    for tod in ('night', 'morn', 'day', 'eve'):
        print("{}: {} {:.1f} +/-{:.1f} [range {:.1f} - {:.1f}; interday +/-{:.1f}] @ {:.0f}%".format(
            locname, tod_strs[tod],
            temps[tod], (spread[tod]/2),
            tranges[tod]['min'], tranges[tod]['max'],
            diffs[tod],
            humidity[tod]))

    #dstr = "{}: evening {:.1f} +/-{:.1f} (d {:.1f}) {:.0f}%".format(locname, temps['night'], (spread['night']/2), diffs['night'], humidity['night'], temps['morn'], (spread['morn']/2), diffs['morn'], humidity['morn'], temps['day'], (spread['day']/2), diffs['day'], humidity['day'], temps['eve'], (spread['eve']/2), diffs['eve'], humidity['eve'])
    #logging.debug(dstr)


# return a list of location id, name records
def getLocations(dbc):
    dbc.execute("SELECT * FROM location")
    results = dbc.fetchall()
    return results


# get date range of observations from the database
def getObservationDateRange(dbc, locid=None):
    if locid:
        wherestr="WHERE location_id={}".format(locid)
    else:
        wherestr = ""

    qry_dates = "SELECT MIN(date), MAX(date), CAST (JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) AS INTEGER) FROM observation {}".format(wherestr)

    dbc.execute(qry_dates)
    row = dbc.fetchone()
    obs_range = {
            'first': row[0],
            'last': row[1],
            'days': row[2]
    }
    return obs_range


# print details of the dates/range being covered
# as provided by getObservationDateRange()
def printObservationDatesSummary(obs_range):
    print("Observations cover {} days, from {} to {}".format(obs_range['days'], obs_range['first'], obs_range['last']))


# calculate the change in avg temps from one day to next
# ideally this would be done with a SQL LAG function
# but sqlite doesn't support it
# ref: https://stackoverflow.com/questions/10003313/create-a-sqlite-view-where-a-row-depends-on-the-previous-row
def calcDayToDayTODAvgTempDiffs(dbc):
    view_str = """
    DROP VIEW IF EXISTS daytoday_avgt_diffs;
    CREATE VIEW daytoday_avgt_diffs AS
    SELECT d1.date as date, d1.tod as tod, d1.name as name,
        d1.ava-d2.ava as tdiff
    FROM
        daily_tod_stats d1, daily_tod_stats d2,
        (SELECT t2.date AS date1, MAX(t1.date) AS date2,
            t1.tod AS tod, t1.name AS name
        FROM daily_tod_stats t1, daily_tod_stats t2
        WHERE t1.date < t2.date
            AND t1.tod = t2.tod
            AND t1.name = t2.name
        GROUP BY t2.date, t2.tod, t2.name) AS prev
    WHERE d1.date = prev.date1 AND d2.date = prev.date2
        AND d1.tod = prev.tod AND d2.tod = prev.tod
        AND d1.name = prev.name AND d2.name = prev.name
    ORDER BY date, tod, name
    ;
    """
    dstr = "calcDayToDayTODAvgTempDiffs() creating view with: {}".format(view_str)
    logging.debug(dstr)

    dbc.executescript(view_str)


# create view of date, time of day stats
def createDailyTODStats(dbc):
    # note use of digit prefix on tod for desired ordering
    # will use a dict to convert results for printing:
    # eg: '1-morn' to 'morning'
    view_str = """
    DROP VIEW IF EXISTS daily_tod_stats;
    CREATE VIEW daily_tod_stats AS
    SELECT date, tod, name, ava, tspread, avr
    FROM (
        SELECT AVG(air_temp) AS ava,
               (MAX(air_temp)-MIN(air_temp)) as tspread,
               AVG(relative_humidity) as avr,
               '0-night' AS tod,
               date, location_id
        FROM datenorm_observation
        WHERE time BETWEEN \"{}\" AND \"24:00\"
           OR time BETWEEN \"00:00\" AND \"{}\"
        GROUP BY date, location_id
        UNION
        SELECT avg(air_temp) AS ava,
               (MAX(air_temp)-MIN(air_temp)) as tspread,
               AVG(relative_humidity) as avr,
               '1-morn' AS tod,
               date, location_id
        FROM datenorm_observation
        WHERE time BETWEEN \"{}\" AND \"{}\"
        GROUP BY date, location_id
        UNION
        SELECT AVG(air_temp) AS ava,
               (MAX(air_temp)-MIN(air_temp)) as tspread,
               AVG(relative_humidity) as avr,
               '2-day' AS tod,
               date, location_id
        FROM datenorm_observation
        WHERE time BETWEEN \"{}\" AND \"{}\"
        GROUP BY date, location_id
        UNION
        SELECT AVG(air_temp) AS ava,
               (MAX(air_temp)-MIN(air_temp)) as tspread,
               AVG(relative_humidity) as avr,
               '3-eve' AS tod,
               date, location_id
        FROM datenorm_observation
        WHERE time BETWEEN \"{}\" AND \"{}\"
        GROUP BY date, location_id
    ) avtable
    INNER JOIN location
    ON location.id = avtable.location_id
    ORDER BY date, tod, name
    """.format(OVERNIGHT_HOUR_START, OVERNIGHT_HOUR_END,
            MORNING_HOUR_START, MORNING_HOUR_END,
            DAYTIME_HOUR_START, DAYTIME_HOUR_END,
            EVENING_HOUR_START, EVENING_HOUR_END)

    dstr = "createDailyTODStats() creating view with: {}".format(view_str)
    logging.debug(dstr)

    dbc.executescript(view_str)


# run an SQL query to get:
#     average, daily change and spread of temperature, relative humidity
# for each date, time interval and location
def getDailyObservations(dbc):
    qrystr = """
    SELECT daily_tod_stats.date AS date,
           daily_tod_stats.tod AS tod,
           daily_tod_stats.name AS name,
           daily_tod_stats.ava as ava,
           daytoday_avgt_diffs.tdiff as tdiff,
           daily_tod_stats.tspread as tspread,
           daily_tod_stats.avr as avr
    FROM daily_tod_stats
    NATURAL LEFT OUTER JOIN daytoday_avgt_diffs
    ORDER BY date, tod, name
    """

    dstr = "getDailyObservations() executing query string: {}".format(qrystr)
    logging.debug(dstr)

    dbc.execute(qrystr)
    rows = dbc.fetchall()
    return rows


# get max and min values for ava for specified loc and tod
def calcRangeTypicalTemps(dbc, locname, tod):
    qrystr = """
    SELECT 
           MIN(ava) AS min_ava,
           MAX(ava) AS max_ava
    FROM daily_tod_stats
    WHERE name = '{}' AND tod = '{}'
    """.format(locname, tod)

    dstr = "calcRangeTypicalTemps() executing query string: {}".format(qrystr)
    logging.debug(dstr)

    dbc.execute(qrystr)
    row = dbc.fetchone()

    trange = {
            'min': float(row[0]),
            'max': float(row[1])
    }
    return trange


# print results obtained from getDailyObservations() query
def printObsByDate(observation_list):
    todname = {
            '0-night': 'overnight',
            '1-morn': 'morning',
            '2-day': 'daytime',
            '3-eve': 'evening',
    }

    dstr = "printObsByDate() observation_list contains {} elements".format(len(observation_list))
    logging.debug(dstr)

    for obs in observation_list:
        # the first day won't have a tdiff value, it will be None
        tdiff = obs['tdiff']
        if tdiff is None:
            tdiff = 0.0
        print("{} {}: {} {:.1f} +/-{:.1f} (d={:.1f}) {:.0f}%".format(
            obs['date'], todname[obs['tod']], obs['name'],
            obs['ava'], (obs['tspread']/2), tdiff, obs['avr']))


# returns dict of dict: tod -> max/min -> value
def getRangeAvgTemps(dbc, loc):
    obsrange = {}
    tods = {
            'night': '0-night',
            'morn': '1-morn',
            'day': '2-day',
            'eve': '3-eve',
    }

    for tod in tods:
        obsrange[tod] = calcRangeTypicalTemps(dbc, loc, tods[tod])

    return obsrange


# create a view to deal with overnight observations that straddle dates
# note that observations start at 10pm (due to crontab script downloading
# at this time), so first date's overnight readings will be complete,
# but last won't - so not included
def create_date_normalised_observations(dbc):
    view_str = """
        DROP VIEW IF EXISTS datenorm_observation;
        CREATE VIEW datenorm_observation AS
        SELECT location_id,
            DATE(observation.date, '+1 day') as date,
            time,
            air_temp,
            apparent_temp,
            relative_humidity,
            cloud_oktas
        FROM observation WHERE time >= TIME(\"{}\")
        AND date < (SELECT MAX(date) FROM observation)
        UNION SELECT location_id,
            date,
            time,
            air_temp,
            apparent_temp,
            relative_humidity,
            cloud_oktas
        FROM observation WHERE time < TIME(\"{}\");
        """.format(OVERNIGHT_HOUR_START, OVERNIGHT_HOUR_START)

    dstr = "create_date_normalised_observations() creating view with: {}".format(view_str)
    logging.debug(dstr)

    dbc.executescript(view_str)

    #dbc.execute(".schema datenorm_observation")
    #rows = dbc.fetchall()
    #for row in rows:
    #    logging.debug(row)


# extract relevant information from observation dictionary
# and add to database
def addObservation(dbc, obs):
    # occasionally data is missing for a location/time
    if obs['air_temp'] is None:
        dstr = "Invalid data! Skipping observation {}".format(obs)
        logging.warn(dstr)
        return
    dstr = "adding observation {} to DB".format(obs)
    logging.debug(dstr)
    location_id = int(obs['wmo'])
    # local_date_time_full is YYYYMMDDHHMMSS
    obsdatetime = datetime.strptime(obs['local_date_time_full'],'%Y%m%d%H%M%S')
    # convert to SQLite date and time compatible string formats
    obs_date = obsdatetime.strftime('%Y-%m-%d')
    obs_time = obsdatetime.strftime('%H:%M:%S')
    air_temp = float(obs['air_temp'])
    apparent_temp = obs['apparent_t']
    if apparent_temp is None:
        apparent_temp = obs['air_temp'] # should be close enough
    apparent_temp = float(apparent_temp )
    relative_humidity = float(obs['rel_hum'])
    cloud_oktas = obs['cloud_oktas']
    if cloud_oktas is None:
        cloud_oktas = '-1' # will ignore in DB select
    cloud_oktas = int(cloud_oktas)
    dbc.execute("INSERT OR IGNORE INTO observation(location_id, date, time, air_temp, apparent_temp, relative_humidity, cloud_oktas) VALUES(?, ?, ?, ?, ?, ?, ?)", (location_id, obs_date, obs_time, air_temp, apparent_temp, relative_humidity, cloud_oktas))


def processObservations(dbc, data):
    dstr = "data contains {} observations".format(len(data))
    logging.debug(dstr)
    if len(data) < 1:
        return 0
    # location details are in each observation record, take from first
    locid = data[0]['wmo']
    locname = data[0]['name']
    dbc.execute("INSERT OR IGNORE INTO location(id, name) VALUES(?, ?)", (locid, locname))
    # add the ordered list of observations to the DB
    for obs in data:
        addObservation(dbc, obs)


# note use of composite key in observation
# as json files may overlap (time based) and cause duplication of data
def initDB(dbc):
    dbc.executescript("""
        DROP TABLE IF EXISTS observation;
        DROP TABLE IF EXISTS location;
        CREATE TABLE location(
            id INTEGER PRIMARY KEY NOT NULL,
            name TEXT, UNIQUE(id, name)
        );
        CREATE TABLE observation(
            location_id INTEGER REFERENCES location(id) NOT NULL,
            date TEXT,
            time TEXT,
            air_temp REAL,
            apparent_temp REAL,
            relative_humidity REAL,
            -- cloud TEXT,
            cloud_oktas INTEGER,
            PRIMARY KEY(location_id, date, time)
        );
    """)

    #dbc.execute(".tables")
    #rows = dbc.fetchall()
    #for row in rows:
    #    logging.debug(row)




##############################################################

def main(argv):

    debug = 0
    paramstr = "[-h] [-d] jsonfile1 [jsonfile 2 ...]"
    usagestr = "Usage: {} {}".format(sys.argv[0], paramstr)

    try:
        options, remainder = getopt.gnu_getopt(argv[1:],"hd")
    except getopt.GetoptError:
        print(usagestr, file=sys.stderr)
        sys.exit(2)

    for opt, arg in options:
        if opt == '-h':
            print(__doc__, file=sys.stderr) # print docstring at start of file
            sys.exit()
        elif opt == '-d':
            debug = 1
        else:
            assert False, "unhandled option"

    # for logging to stderr (by default on level WARN and above)
    if debug>0:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)

    dstr = "number of remaining args = {}; args = {}".format(len(remainder), str(remainder))
    logging.debug(dstr)

    if (len(remainder) < 1):
        print(usagestr)
        sys.exit(2)

    dstr = "{} json files to process".format(len(remainder))
    logging.info(dstr)

    # if running in debug mode, create database file
    if debug:
        # create temporary filename in current working directory
        #pid = os.getpid() 
        cwd = os.getcwd()
        with tempfile.NamedTemporaryFile(delete=False, dir=cwd, suffix='.sqlite') as tmpf:
            tempfname = tmpf.name
        dstr = "using temp file {} for database".format(tempfname)
        logging.info(dstr)
        conn = sqlite3.connect(tempfname) # temp db on file
    else: # otherwise create database in memory
        #conn = sqlite3.connect(':memory:') # create db solely in memory
        conn = sqlite3.connect('') # temp db, in mem but can use swap

    with conn:
        # use a dictionary cursor
        conn.row_factory = sqlite3.Row
        dbc = conn.cursor()
        initDB(dbc)

        # TODO: process rainfall readings, wind direction and speed

        # process the provided json files - extracting observations
        for fn in remainder:
            dstr = "processing file {}".format(fn)
            logging.debug(dstr)
            # read json file into dictionary
            with open(fn, 'r') as f:
                data = json.load(f)
            processObservations(dbc, data['observations']['data'])

        # normalise dates to deal with overnight observations
        create_date_normalised_observations(dbc)

        # generate daily stats for each time of day
        createDailyTODStats(dbc)
        # and diffs between consecutive days
        calcDayToDayTODAvgTempDiffs(dbc)
        # get a day by day observation report for all locations
        daily_obs_list = getDailyObservations(dbc)
        printObsByDate(daily_obs_list)

        # display the date range for the following location summaries
        obs_range = getObservationDateRange(dbc)
        printObservationDatesSummary(obs_range)

        # calc typical temps, temp spread, cloudiness for each location
        locations = getLocations(dbc) # list of location records
        for loc in locations:
            typical_temps = calcTypicalTemps(dbc, loc['id'], 'AVG')
            #min_temps = calcTypicalTemps(dbc, loc['id'], 'MIN')
            #max_temps = calcTypicalTemps(dbc, loc['id'], 'MAX')
            temp_range = getRangeAvgTemps(dbc, loc['name'])
            typical_spread = calcTypicalTempSpread(dbc, loc['id'])
            typical_tdiff = calcTypicalTempDiff(dbc, loc['name'])
            typical_humidity = calcTypicalHumidity(dbc, loc['id'])
            typical_cloud = calcCloudiness(dbc, loc['id'])
            printLocationSummary(loc['name'], typical_temps, temp_range, typical_spread, typical_tdiff, typical_humidity, typical_cloud)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

