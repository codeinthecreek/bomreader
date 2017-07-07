#!/bin/bash

usage_str="Usage: $(basename $0) [field-options] [filename]"
if [ $# -eq 0 ]; then
    echo >&2 "$usage_str"
    echo >&2 "Field options available: tahdwrcp"
    echo >&2 "    t: air_temp; a: apparent_t; h: rel_hum; d: dewpt;"
    echo >&2 "    w: wind_dir wind_spd_kmh; r: rain_trace; c: cloud; p: press_msl"
    echo >&2 "if filename isn't supplied then standard input is assumed"
    exit 0
fi

fieldstr="\\(.name) \\(.local_date_time) : \\(.air_temp) feels like \\(.apparent_t)"

#while getopts tahdwrcpo: opt; do
while getopts tahdwrcp opt; do
    case "$opt" in
        t) # air_temp
            echo "temperature is displayed by default"
            ;;
        a) # apparent_t
            echo "apparent temperature is displayed by default"
            ;;
        h) # rel_hum
            fieldstr="${fieldstr} humidity: \\(.rel_hum)"
            ;;
        d) # dewpt
            fieldstr="${fieldstr} dewpoint: \\(.dewpt)"
            ;;
        w) # wind_dir wind_spd_kmh
            fieldstr="${fieldstr} wind: \\(.wind_dir) \\(.wind_spd_kmh)"
            ;;
        r) # rain_trace
            fieldstr="${fieldstr} rain: \\(.rain_trace)"
            ;;
        c) # cloud
            fieldstr="${fieldstr} cloud: \\(.cloud)"
            ;;
        p) # press_msl
            fieldstr="${fieldstr} barometer: \\(.press_msl)"
            ;;
        #o) # write to file
        #    outfile="$OPTARG"
        #    ;;
    esac
done

# get rid of option params
shift $((OPTIND-1))

echo "using filter: $fieldstr"
echo "number of file arguments remaining: $#"

if [ $# -eq 0 ]; then
    filename="-"
else
    filename=$1
    shift
fi

while [ -n "$filename" ]; do
    echo "processing file: $filename"
    #cat $filename | jq -r '.observations.data[] | "\(.name) \(.local_date_time) : \(.air_temp) feels like \(.apparent_t)"' | head

    # note in following to expand bash variable within single quotes
    # close the single quote, double quote variable, then reopen single quote
    # the preceding and following double quotes are part of the command
    # as per: jq -r '.observations.data[] | "\(.local_date_time) : \(.air_temp)"'
    jq -r '.observations.data[] | "'"${fieldstr}"'"' $filename
    #echo "done with exit code: $?"
    filename=""
    if [ $# -gt 0 ]; then
        filename=$1
        shift
    fi
done

