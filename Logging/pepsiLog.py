#!/usr/bin/env python3
'''
pepsiLog - make a PEPSI data log for a night

Usage: pepsiLog ccyymmdd

Creates ccyymmdd_pepsi.txt in logDir

R. Pogge, OSU Astronomy
pogge.1@osu.edu
2024 June 30

Modified: 2024 June 30
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
    print('Usage: pepsiLog CCYYMMDD')
    sys.exit(0)

# Hard coded PEPSI logging info

fitsKeys = ['PROPID','ARM','IMAGETYP','OBJECT','LBTRA','LBTDE','EXPTIME','DATE-OBS','TIME-OBS',
            'AIRMASS','FIBER','CROSDIS','FILENAME']

keyFmts = ['20.20s','4.4s','7.7s','40.40s','11.11s','11.11s','6.1f','10.10s','10.10s','4.2f','3.3s',
           '14.14s','25.25s']

tabHeads = ['ProjectID','ARM','ImgTyp','Object','RA','Dec','Exp','UTCDate','UTCTime','SecZ','Fib',
            'CD  LamRange','Filename']

tabFmts = ['20.20s','4.4s','7.7s','40.40s','11.11s','11.11s','6.6s','10.10s','10.10s','4.4s','3.3',
           '14.14s','25.25s']

# A valid repository directory?

dataDir = f'{repoDir}/{obsDate}'

if not os.path.isdir(dataDir):
    print(f'Could not find data directory {obsDate} in {repoDir}')
    print(f'Usage: pepsiLog ccyymmdd')
    sys.exit(1)

# Get a list of all pepsi data matching pattern

pepsiFiles = glob.glob(f'{repoDir}/{obsDate}/pepsi?.{obsDate}.*.fits')

if len(pepsiFiles) == 0:
    print(f'No PEPSI FITS files found in directory {obsDate} in {repoDir}')
    print(f'No PEPSI data log created.')
    sys.exit(1)

# start the PEPSI log

logFile = f'{logDir}/{obsDate}_pepsi.txt'

ml = open(logFile,'w')

hdrStr = ''
for i in range(len(tabHeads)):
    hdrStr += f'{tabHeads[i]:{tabFmts[i]}} '

ml.write(f'{hdrStr}\n')
#print(f'{hdrStr}')

numCal = 0

for fitsFile in pepsiFiles:
    hdr = getheader(fitsFile)
    if hdr['PARTNER'].upper() == 'CALIBRATION':
        numCal += 1
    else:
        outStr = ''
        for i in range(len(fitsKeys)):
            if fitsKeys[i] == 'FILENAME':
                keyData = os.path.splitext(os.path.split(fitsFile)[1])[0]
            else:
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
print(f'Done: wrote {len(pepsiFiles)} records to {logFile}')

sys.exit(0)
