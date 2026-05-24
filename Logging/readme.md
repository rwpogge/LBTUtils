# Data Logging Scripts

These are scripts used to create observing data logs for a night.  They include python scripts that scrape raw image FITS
headers to create instrument-specific data logs in our standard ASCII text format, and to retrieve LBT telemetry data
for the guide cameras (GCS) and environmental (weather) sensors for a night.

## Contents

 * `modsLog.py` - make a MODS data log
 * `luciLog.py` - make a LUCI data log
 * `lbcLog.py` - make an LBC data log
 * `pepsiLog.py` - make a PEPSI data log
 * `getEnv.py` - retrieve LBT weather telemetry files (hdf5)
 * `getGCS.py` - retrieve LBT guider telemetry files (hdf5)
