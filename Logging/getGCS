#!/bin/csh 
#
# New paths for 2024B [rwp/osu]
# 

set dataDir = /lbt/data/telemetry/tcs
set logDir = /home/osurc/share/ObsLogs/GCS

if ($#argv != 3) then
   echo "Usage: getGCS ccyy mm dd"
   echo "       copies the GCS logs into $logDir"
   exit 1
endif

set ccyy = $1
set mm = $2
set dd = $3

cp ${dataDir}/gcs?/${ccyy}/${mm}/${dd}/*guiding.h5 ${logDir}

echo  " "
echo "Done: GCS logs in ${logDir}"
echo " "
exit 0
