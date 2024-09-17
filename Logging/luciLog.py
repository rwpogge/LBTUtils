#!/usr/bin/env python3
'''
luciLog - make a LUCI data log for a night

Usage: luciLog ccyymmdd

Creates ccyymmdd_luci.txt in logDir

R. Pogge, OSU Astronomy
pogge.1@osu.edu
2022 Sept 24

Modified: 2022 Sept 24
'''

import sys
import os
import glob

# fast FITS header access:

from astropy.io.fits import getheader

# throttle nuisance warnings

import warnings
warnings.filterwarnings('ignore',category=UserWarning, append=True)
warnings.filterwarnings('ignore',category=RuntimeWarning, append=True)

# where is the raw data repository?

repoDir = '/lbt/data/repository'

# where do logs go

logDir = '/home/osurc/share/ObsLogs'

# get command line arguments

if len(sys.argv) == 2:
    obsDate = sys.argv[1]
else:
    print('Usage: luciLog CCYYMMDD')
    sys.exit(0)

# Hard coded LUCI logging info

fitsKeys = ['PROPID','OBJECT','OBJRA','OBJDEC','POSANGLE','EXPTIME','DATE-OBS','TELALT','MASKNAME',
            'GRATNAME','CAMNAME','FILTER1','FILTER2','FILENAME']

keyFmts = ['20.20s','16.16s','11.11s','11.11s','6.1f','6.1f','21.21s','6.1f','12.12s',
           '9.9s','5.5s','9.9s','9.9s','25.25s']

tabHeads = ['ProjectID','Object','RA','Dec','PA','Exp','UTCDate/Time','TelAlt','MaskName',
            'Grating','Filter1','Filter2','Filename']

tabFmts = ['20.20s','16.16s','11.11s','11.11s','6.6s','6.6s','21.21s','6.6s','12.12s',
           '9.9s','5.5s','9.9s','9.9s','25.25s']

# A valid repository directory?

dataDir = f'{repoDir}/{obsDate}'

if not os.path.isdir(dataDir):
    print(f'Could not find data directory {obsDate} in {repoDir}')
    print(f'Usage: luciLog ccyymmdd')
    sys.exit(1)

# Get a list of all luci data matching pattern

luciFiles = glob.glob(f'{repoDir}/{obsDate}/luci?.{obsDate}.*.fits')

if len(luciFiles) == 0:
    print(f'No LUCI FITS files found in directory {obsDate} in {repoDir}')
    print(f'No LUCI data log created.')
    sys.exit(1)

# start the LUCI log

logFile = f'{logDir}/{obsDate}_luci.txt'

ml = open(logFile,'w')

hdrStr = ''
for i in range(len(tabHeads)):
    hdrStr += f'{tabHeads[i]:{tabFmts[i]}} '

ml.write(f'{hdrStr}\n')
#print(f'{hdrStr}')

for fitsFile in luciFiles:
    hdr = getheader(fitsFile)

    outStr = ''
    for i in range(len(fitsKeys)):
        try:
            keyData = hdr[fitsKeys[i]]
        except:
            keyData = ''
        try:
            outStr += f'{keyData:{keyFmts[i]}} '
        except:
            outStr += f'{keyData:{tabFmts[i]}} '

    ml.write(f'{outStr}\n')
    #print(outStr)
    
ml.close()
print(f'Done: wrote {len(luciFiles)} records to {logFile}')

sys.exit(0)
