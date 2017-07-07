#!/bin/bash

declare -A locations
locations=( \
    ["Brisbane_AP"]="94578" \
    ["Rockhampton"]="94374" \
    ["Mackay_AP"]="95367" \
    ["Proserpine"]="94365" \
    ["Bowen_AP"]="94383" \
    ["Townsville_AP"]="94294" \
    ["Innisfail_AP"]="94280" \
    ["Cairns"]="94287" \
    ["Cairns_RC"]="94288" \
    ["Mareeba"]="95286" \
    ["Cooktown"]="95283" \
)

declare -A equivlocs
equivlocs=( \
    ["brisbane"]="Brisbane_AP" \
    ["bne"]="Brisbane_AP" \
    ["rockhampton"]="Rockhampton" \
    ["rok"]="Rockhampton" \
    ["mackay"]="Mackay_AP" \
    ["mky"]="Mackay_AP" \
    ["proserpine"]="Proserpine" \
    ["bowen"]="Bowen_AP" \
    ["townsville"]="Townsville_AP" \
    ["tsv"]="Townsville_AP" \
    ["innisfail"]="Innisfail_AP" \
    ["cairns"]="Cairns_RC" \
    ["cns"]="Cairns" \
    ["mareeba"]="Mareeba" \
    ["cooktown"]="Cooktown" \
)

if [ $# -gt 0 ]; then
    loc=${equivlocs[$1]} # check if a shorthand has been used first
    [ -z "$loc" ] && loc=$1
    lcode=${locations[$loc]}
    shift
fi

if [ -z "$lcode" ]; then
    usage_str="Usage: $(basename $0) location"
    loclist=""
    for key in ${!locations[@]}; do
        #echo ${key} ${locations[${key}]}
        # add space separator if loclist already has an element
        loclist="${loclist:+$loclist }${key}"
    done
    eloclist=""
    for key in ${!equivlocs[@]}; do
        # add space separator if loclist already has an element
        eloclist="${eloclist:+$eloclist }${key}"
    done
    echo >&2 "$usage_str"
    echo >&2 "Invalid location specified! Please chooose from: $loclist"
    echo >&2 "Or equivalents: $eloclist"
    exit 1
fi

echo >&2 "location chosen is $loc with code $lcode"
echo >&2 "retrieving URL http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.${lcode}.json"
echo >&2 "writing to file ${loc}-$(/bin/date +\%F).json"

#echo curl "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.${lcode}.json" ">" "${loc}-$(/bin/date +\%F)"
curl "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.${lcode}.json" 2>/dev/null > "${loc}-$(/bin/date +\%F)".json

echo >&2 "done!"


