#!/usr/bin/env python3
'''
modsLog - make a MODS data log for a night

Usage: modsLog ccyymmdd

Creates ccyymmdd_mods.txt in logDir

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
    print('Usage: modsLog CCYYMMDD')
    sys.exit(0)

# Hard coded MODS logging info

fitsKeys = ['PROPID','CHANNEL','IMAGETYP','OBJECT','TELRA','TELDEC','POSANGLE','EXPTIME','DATE-OBS',
            'AIRMASS','MASKNAME','DICHNAME','GRATNAME','FILTNAME','FILENAME']

keyFmts = ['20.20s','4.4s','7.7s','40.40s','11.11s','11.11s','6.1f','6.1f','21.21s','5.2f','12.12s','4.4s',
           '5.5s','7.7s','25.25s']

tabHeads = ['ProjectID','Chan','ImgTyp','Object','RA','Dec','PA','Exp','UTCDate/Time','SecZ','SlitMask',
            'Mode','Grat','Filter','Filename']

tabFmts = ['20.20s','4.4s','7.7s','40.40s','11.11s','11.11s','6.6s','6.6s','21.21s','5.5s','12.12s','4.4s',
           '5.5s','7.7s','25.25s']

# A valid repository directory?

dataDir = f'{repoDir}/{obsDate}'

if not os.path.isdir(dataDir):
    print(f'Could not find data directory {obsDate} in {repoDir}')
    print(f'Usage: modsLog ccyymmdd')
    sys.exit(1)

# Get a list of all mods data matching pattern

modsFiles = glob.glob(f'{repoDir}/{obsDate}/mods??.{obsDate}.*.fits')

if len(modsFiles) == 0:
    print(f'No MODS FITS files found in directory {obsDate} in {repoDir}')
    print(f'No MODS data log created.')
    sys.exit(1)

# start the MODS log

logFile = f'{logDir}/{obsDate}_mods.txt'

ml = open(logFile,'w')

hdrStr = ''
for i in range(len(tabHeads)):
    hdrStr += f'{tabHeads[i]:{tabFmts[i]}} '

ml.write(f'{hdrStr}\n')
#print(f'{hdrStr}')

for fitsFile in modsFiles:
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
print(f'Done: wrote {len(modsFiles)} records to {logFile}')

sys.exit(0)
