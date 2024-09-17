#!/usr/bin/env python3
'''
lbcLog - make a LBC data log for a night

Usage: lbcLog ccyymmdd

Creates ccyymmdd_lbc.txt in logDir

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
    print('Usage: lbcLog CCYYMMDD')
    sys.exit(0)

# Hard coded LBC logging info

fitsKeys = ['PROPID','IMAGETYP','OBJECT','OBSRA','OBSDEC','EXPTIME','DATE_OBS','AIRMASS',
            'FILTER','LBCOBNAM','FILENAME']

keyFmts = ['20.20s','8.8s','16.16s','10.10s','10.10s','6.1f','21.21s','5.2f','9.9s',
           '20.02s','25.25s']

tabHeads = ['ProjectID','ImageTyp','Object','RA','Dec','Exp','UTCDate/Time','SecZ',
            'Filter','OB','Filename']

tabFmts = ['20.20s','8.8s','16.16s','10.10s','10.10s','6.6s','21.21s','5.5s','9.9s',
           '20.02s','25.25s']

# A valid repository directory?

dataDir = f'{repoDir}/{obsDate}'

if not os.path.isdir(dataDir):
    print(f'Could not find data directory {obsDate} in {repoDir}')
    print(f'Usage: lbcLog ccyymmdd')
    sys.exit(1)

# Get a list of all LBC data matching pattern

lbcFiles = glob.glob(f'{repoDir}/{obsDate}/lbc?.{obsDate}.*.fits')

if len(lbcFiles) == 0:
    print(f'No LBC FITS files found in directory {obsDate} in {repoDir}')
    print(f'No LBC data log created.')
    sys.exit(1)

# start the LBC log

logFile = f'{logDir}/{obsDate}_lbc.txt'

ml = open(logFile,'w')

hdrStr = ''
for i in range(len(tabHeads)):
    hdrStr += f'{tabHeads[i]:{tabFmts[i]}} '

ml.write(f'{hdrStr}\n')
#print(f'{hdrStr}')

for fitsFile in lbcFiles:
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
print(f'Done: wrote {len(lbcFiles)} records to {logFile}')

sys.exit(0)
