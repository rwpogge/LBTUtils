#!/usr/bin/env python

'''
gcsPlot - plot LBT AGw data for a night

Usage
-----
   gcsPlot CCYYMMDD

Description
-----------
   Opens and plots the contents of an LBT GCS (Guide Control System) telemetry file
   for a night.  It makes a multipanel plot showing the average seeing measured
   by the guider and transparency for a night

   Creates plot file `CCYYMMDD_gcs.png`

   GCS telemetry data are stored as HDF5 format files copied from the
   /lbt/data/telemetry/tcs/gcs/ folder on the summit computers
   using the `getGCS` python script on the osurc user account

Author
------
   R. Pogge, OSU Astronomy Dept.
   pogge.1@osu.edu

Modification History
--------------------
   2026 May 24 - standalone script from the Jupyter notebook source [rwp/osu]


'''

import os
import sys
import math
import h5py as hdf
import numpy as np
import glob
import getopt

# plotting

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, LogLocator, NullFormatter

# astropy time 

from astropy.time import Time

# scipy uniform_filter1d() method for running means

from scipy.ndimage import uniform_filter1d

# observing circumstances for annotation with sunrise/sunset etc.

import thorsky.thorskyclasses3 as tsc3
import thorsky.thorskyutil as tsu

# throttle nuisance warnings

import warnings
warnings.filterwarnings('ignore',category=UserWarning, append=True)
warnings.filterwarnings('ignore',category=RuntimeWarning, append=True)

# Version info

versNum = '1.0.1'
versDate = '2026-05-24'

# Usage message

def printUsage():
    '''
    print a usage message for this program
    '''
    print("\nUsage: gcsPlot CCYYMMDD [options]")
    print("\nWhere:")
    print("   CCYYMMDD - observing date (part of the HDF5 filenames)")
    print("\nOptions:")
    print("   -w fwMax = specify the max FWHM to plot (default: auto range)")
    print("   -v = verbose output")
    print("   -V = print version info and exit")

# Default options

haveSX = False
haveDX = False
verbose = False
fwAuto = True

# Parse the command line (GNU-style getopt)

try:
    opts, files = getopt.gnu_getopt(sys.argv[1:],'w:vV',
                                  ['fwmax','verbose','version'])
except getopt.GetoptError as err:
    print(f'\n** ERROR: {err}')
    printUsage()
    sys.exit(2)

if len(opts)==0 and len(files)==0:
    printUsage()
    sys.exit(1)

for opt, arg in opts:
    if opt in ('-V','--version'):
        print(f"envPlot v{versNum} [{versDate}]")
        sys.exit(0)

    elif opt in ('-v','--verbose'):
        verbose = True

    elif opt in ('-w','--width'):
        try:
            fwMax = float(arg)
            fwAuto = False
        except Exception as exp:
            print(f"ERROR: invalid {opt} value, must be a number")
            printUsage()
            sys.exit(1)

# observing date

numFiles = len(files)

if numFiles < 1:
  printUsage()
  sys.exit(1)

dateTag = files[0]
if len(dateTag) != 8:
    print(f"ERROR: date must be CCYYMMDD including leading zeros (e.g., 20260524)")
    printUsage()
    sys.exit(1)

try:
    obsYear = dateTag[0:4]
    obsMon = dateTag[4:6]
    obsDay = dateTag[6:8]
except Exception as exp:
    print(f"ERROR: invalid observing date '{dateTag}', must be CCYYMMDD")
    printUsage()
    sys.exit(1)

obsDate = f"{obsYear}{obsMon}{obsDay}" # for filenames
obsUTC = f"{obsYear}-{obsMon}-{obsDay}" # for time calculations

# Standard plot setup

# Plot width and height in pixels

plotHeight = 4000
plotWidth = 3000

# Font and line weight defaults for axes

lwidth = 0.5
matplotlib.rcParams.update({'font.size':8})
matplotlib.rc('axes',linewidth=lwidth)

# LaTeX will be used throughout for markup of symbols

plt.rc('text', usetex=True)
plt.rc('font', **{'family':'serif','serif':['Times-Roman'],'weight':'bold','size':'8'})
plt.rcParams['xtick.major.pad']='5'
plt.rcParams['ytick.major.pad']='5'
plt.rcParams['axes.labelpad'] = '5'

# plot resolution and window

dpi = 600
wDisp = plotWidth
hDisp = plotHeight
wInches = float(wDisp)/float(dpi)
hInches = float(hDisp)/float(dpi)

# Open and read the hdf5 files

sxList = glob.glob(f'GCS/{obsDate}*.gcsl.guiding.h5')
if len(sxList)==1:
    sxFile = sxList[0]
    haveSX = True
else:
    sxFile = 'gcsl.h5'
    
dxList = glob.glob(f'GCS/{obsDate}*.gcsr.guiding.h5')
if len(dxList)==1:
    dxFile = dxList[0]
    haveDX = True
else:
    dxFile = 'gcsr.h5'

# open the HDF files

if haveSX:
    gcsl = hdf.File(sxFile,'r') # read only
if haveDX:
    gcsr = hdf.File(dxFile,'r')

if haveSX:
    sxDS = list(gcsl.keys())[0]
    sxData = gcsl[sxDS]

    if verbose:
        for datum in ['time_stamp','avgseeing','sxellip','sxflux','exptime']:
            print(f'\n{datum}:')
            for key in ['Description','Units']:
                print(f"  {key}: {sxData.attrs[key][datum]}")

    sxMJD = sxData['time_stamp']*1.0e-6/86400.0 # convert MJD in microseconds to days
    mjd0 = int(sxMJD[0])
    sxHour = 24.0*(sxMJD-mjd0)

    sxFWHM = sxData['avgseeing']
    sxEll = sxData['sxellip']
    sxFlux = sxData['sxflux']
    sxExpT = 1.0e-3*sxData['exptime']
    sxMag = 27.0 - 2.5*np.log10(sxFlux/sxExpT)

if haveDX:
    dxDS = list(gcsr.keys())[0]
    dxData = gcsr[dxDS]

    dxMJD = dxData['time_stamp']*1.0e-6/86400.0 # convert MJD in microseconds to days
    if not haveSX:
        mjd0 = int(dxMJD[0])
    
    dxHour = 24.0*(dxMJD-mjd0)

    dxFWHM = dxData['avgseeing']
    dxEll = dxData['sxellip']
    dxFlux = dxData['sxflux']
    dxExpT = 1.0e-3*dxData['exptime']
    dxMag = 27.0 - 2.5*np.log10(dxFlux/dxExpT)

# UTC date from the starting MJD

t = Time([mjd0], format='mjd', scale='utc')
utcDate = f"{t.to_value('iso',subfmt='date')[0]}"

# plotting limits

if not haveSX:
    minTime = np.min(dxHour)
    maxTime = np.max(dxHour)
    medFWHM = np.median(dxFWHM)
    minMag = np.nanmin(dxMag)
    maxMag = np.nanmax(dxMag)
elif not haveDX:
    minTime = np.min(sxHour)
    maxTime = np.max(sxHour)
    medFWHM = np.median(sxFWHM)
    minMag = np.nanmin(sxMag)
    maxMag = np.nanmax(sxMag)
else:
    minTime = np.min([np.min(sxHour),np.min(dxHour)])
    maxTime = np.max([np.max(sxHour),np.max(dxHour)])
    medFWHM = np.max([np.median(sxFWHM),np.median(dxFWHM)])
    minMag = np.min([np.nanmin(dxMag),np.nanmin(sxMag)])
    maxMag = np.min([np.nanmax(dxMag),np.nanmax(sxMag)])
    
dT = maxTime - minTime
tMin = np.floor(minTime) # minTime - 0.05*dT
tMax = np.ceil(maxTime+0.01*dT) # maxTime + 0.05*dT
#tMin = 7.5
#tMax = 7.5

fwMin = 0.0
if fwAuto:
    fwMax = np.ceil(2.0*medFWHM)
if verbose:
    print(f'fwMax={fwMax:.2f} arcsec')

if verbose:
    print(f'minMag={minMag:.2f}, maxMax={maxMag:.2f}')
    
dm = maxMag - minMag
mMin = np.ceil(maxMag + 0.05*dm)
mMax = np.floor(minMag - 0.05*dm)

# make a plot

fig,(ax1,ax2) = plt.subplots(2,1,figsize=(wInches,hInches),dpi=dpi)
fig.subplots_adjust(wspace=0, hspace=0.2)

# Top panel - image quality

ax1.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
ax1.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

# Limits

ax1.set_ylabel(r'FWHM [arcsec] \& ellipticity')

ax1.xaxis.set_major_locator(MultipleLocator(1.0))
ax1.xaxis.set_minor_locator(MultipleLocator(0.25))
ax1.set_xlim(tMin,tMax)

ax1.yaxis.set_major_locator(MultipleLocator(0.5))
ax1.yaxis.set_minor_locator(MultipleLocator(0.1))
ax1.set_ylim(fwMin,fwMax)

if haveSX:
    ax1.plot(sxHour,sxFWHM,marker='o',mfc='black',ms=1,zorder=10,mew=0,lw=0,label='SX guider')
    ax1.plot(sxHour,sxEll,marker='o',color='black',ms=0.5,mew=0,zorder=10,lw=0,alpha=0.5)
if haveDX:
    ax1.plot(dxHour,dxFWHM,marker='o',mfc='green',ms=1,zorder=10,mew=0,lw=0,label='DX guider')
    ax1.plot(dxHour,dxEll,marker='o',color='green',ms=0.5,mew=0,zorder=10,lw=0,alpha=0.5)

ax1.set_title(rf'LBT AGw guide star data for {utcDate} UTC',fontsize=10)
ax1.legend(fontsize=8,markerscale=3)

# Bottom Panel - photometry

ax2.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
ax2.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

# Limits

ax2.set_xlabel(rf'Time (UT Hours) for {utcDate} UTC')
ax2.set_ylabel(r'Instrumental R Mag')

ax2.xaxis.set_major_locator(MultipleLocator(1.0))
ax2.xaxis.set_minor_locator(MultipleLocator(0.25))
ax2.set_xlim(tMin,tMax)

ax2.yaxis.set_major_locator(MultipleLocator(1.0))
ax2.yaxis.set_minor_locator(MultipleLocator(0.2))
ax2.set_ylim(mMin,mMax)

if haveSX:
    ax2.plot(sxHour,sxMag,marker='o',mfc='black',ms=1,zorder=10,mew=0,lw=0)
if haveDX:
    ax2.plot(dxHour,dxMag,marker='o',mfc='green',ms=1,zorder=10,mew=0,lw=0)

plt.plot()

# hardcopy

plotFile = f'{obsDate}_gcs.png'
plt.savefig(plotFile,bbox_inches='tight',facecolor='white')

# all done

print(f"DONE: plotting GCS data for {utcDate} UTC")

sys.exit(0)
