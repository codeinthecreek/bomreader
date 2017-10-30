#!/bin/bash

# Note:
# Qld observations accessed through: http://www.bom.gov.au/qld/observations/qldall.shtml
# NT observations accessed through: http://www.bom.gov.au/nt/observations/ntall.shtml

declare -A locations
locations=( \
    ["Brisbane_AP"]="94578" \
    ["Rockhampton"]="94374" \
    ["Mackay_AP"]="95367" \
    ["Proserpine"]="94365" \
    ["Bowen_AP"]="94383" \
    ["Townsville_AP"]="94294" \
    ["Townsville_MS"]="94272" \
    ["Innisfail_AP"]="94280" \
    ["Cairns"]="94287" \
    ["Cairns_RC"]="94288" \
    ["Mareeba"]="95286" \
    ["Cooktown"]="95283" \
    ["Darwin_AP"]="94120" \
)

declare -A statecodes
statecodes=( \
    ["Brisbane_AP"]="IDQ60801/IDQ60801" \
    ["Rockhampton"]="IDQ60801/IDQ60801" \
    ["Mackay_AP"]="IDQ60801/IDQ60801" \
    ["Proserpine"]="IDQ60801/IDQ60801" \
    ["Bowen_AP"]="IDQ60801/IDQ60801" \
    ["Townsville_AP"]="IDQ60801/IDQ60801" \
    ["Townsville_MS"]="IDQ60801/IDQ60801" \
    ["Innisfail_AP"]="IDQ60801/IDQ60801" \
    ["Cairns"]="IDQ60801/IDQ60801" \
    ["Cairns_RC"]="IDQ60801/IDQ60801" \
    ["Mareeba"]="IDQ60801/IDQ60801" \
    ["Cooktown"]="IDQ60801/IDQ60801" \
    ["Darwin_AP"]="IDD60801/IDD60801" \
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
    ["Townsville"]="Townsville_AP" \
    ["tsv"]="Townsville_AP" \
    ["townsville_ms"]="Townsville_MS" \
    ["MtStuart"]="Townsville_MS" \
    ["mtstuart"]="Townsville_MS" \
    ["innisfail"]="Innisfail_AP" \
    ["cairns_rc"]="Cairns_RC" \
    ["cairns_ap"]="Cairns" \
    ["Cairns_AP"]="Cairns" \
    ["cns"]="Cairns" \
    ["mareeba"]="Mareeba" \
    ["cooktown"]="Cooktown" \
    ["darwin"]="Darwin_AP" \
    ["Darwin"]="Darwin_AP" \
)

if [ $# -gt 0 ]; then
    loc=${equivlocs[$1]} # check if a shorthand has been used first
    [ -z "$loc" ] && loc=$1
    scode=${statecodes[$loc]}
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
echo >&2 "retrieving URL http://www.bom.gov.au/fwo/${scode}.${lcode}.json"
echo >&2 "writing to file ${loc}-$(/bin/date +\%F).json"

#echo curl "http://www.bom.gov.au/fwo/${scode}.${lcode}.json" ">" "${loc}-$(/bin/date +\%F)"
curl "http://www.bom.gov.au/fwo/${scode}.${lcode}.json" 2>/dev/null > "${loc}-$(/bin/date +\%F)".json

echo >&2 "done!"


