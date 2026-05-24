#!/usr/bin/env python

'''
envPlot - plot LBT environmental log data for a night

Usage
-----
   envPlot CCYYMMDD

Description
-----------
   Opens and plots the contents of an LBT environmental log file
   for a night.  It makes two plots
    * A multipanel plot of temperature, humidity, wind speed, and pressure
    * A wind-rose plot showing wind speed and direction

   Creates two plot files:
    * Weather data: `CCYYMMDD_env.png`
    * Wind Rose: `CCYYMMDD_wind.png`

   Plots are annotated with the relevant limits (humidity and wind speed)
   that affect opening the enclosure.

   Weather data are stored as HDF5 format files copied from the
   /lbt/data/telemetry/tcs/env/ folder on the summit computers
   using the `getEnv` python script on the osurc user account

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
    print("\nUsage: envPlot CCYYMMDD [options]")
    print("\nWhere:")
    print("   CCYYMMDD - observing date (part of the HDF5 filenames)")
    print("\nOptions:")
    print("   -a = plot all times, not just nighttime")
    print("   -w = include plot of precipitable water vapor (SMT)")
    print("   -d = plot dewpoint (default: no dewpoint)")
    print("   -s = plot sunset/twilight/sunrise times")
    print("   -v = verbose output")
    print("   -V = print version info and exit")

# Default options

plotPWV = False
plotDewPt = False
nightOnly = True
plotSun = False
startUTC = 0.0
endUTC = 14.0
verbose = False

# Parse the command line (GNU-style getopt)

try:
    opts, files = getopt.gnu_getopt(sys.argv[1:],'awdsvV',
                                  ['all','pwv','dewpoint','sun','verbose','version'])
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

    elif opt in ('-w','--pwv'):
        plotPWV = True
        
    elif opt in ('-a','--all'):
        nightOnly = False
        
    elif opt in ('-d','--dewpoint'):
        plotDewPt = True
        
    elif opt in ('-s','--sun'):
        plotSun = True

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

# plot LBT environmental sensor data - see the Jupyter notebook for details

# instantiate an obs object for LBT

obs = tsc3.Observation(site='lbt')  

tz = obs.site.localtz
obs.settime(f'{obsDate} 23:59:59')
obs.computesky()
obs.computesunmoon()
obs.setnightevents()
sunset = obs.tsunset.to_datetime() 
endtwi12 = obs.tevetwi12.to_datetime() 
endtwi = obs.tevetwi.to_datetime()
begtwi = obs.tmorntwi.to_datetime()
begtwi12 = obs.tmorntwi12.to_datetime()
sunrise = obs.tsunrise.to_datetime()
moonrise = obs.tmoonrise.to_datetime()
moonset = obs.tmoonset.to_datetime()

if verbose:
    print(f"Sunset: {sunset}, Sunrise: {sunrise}")

# sunrise/sunset/twilight UTC times in decimal hours

srUTC = sunrise.hour + sunrise.minute/60 + sunrise.second/3600
end12 = endtwi12.hour + endtwi12.minute/60 + endtwi12.second/3600
end18 = endtwi.hour + endtwi.minute/60 + endtwi.second/3600 
beg18 = begtwi.hour + begtwi.minute/60 + begtwi.second/3600 
beg12 = begtwi12.hour + begtwi12.minute/60 + begtwi12.second/3600
ssUTC = sunset.hour + sunset.minute/60 + sunset.second/3600

sstTimes = [srUTC,end12,end18,beg18,beg12,ssUTC]
timeStr = ['SS','t12','t18','d18','d12','SR']

# get the data files (hdf5)

lbtList = glob.glob(f'Env/{obsDate}*.env.lbt_weather.h5')
if len(lbtList)==1:
    lbtFile = lbtList[0]
else:
    lbtFile = 'lbtEnv.h5'
    
smtList = glob.glob(f'Env/{obsDate}*.env.smt_weather.h5')
if len(smtList)==1:
    smtFile = smtList[0]
else:
    smtFile = 'smtEnv.h5'

# LBT Evironmental Data

lbtEnv = hdf.File(lbtFile,'r') # read only
lbtDS = list(lbtEnv.keys())[0]
if verbose:
    print(lbtDS)
lbtData = lbtEnv[lbtDS]

if verbose:
    print(lbtData.dtype) # uncomment to see all data values
    print("\nLBT Env Data:")
    for datum in ['time_stamp','temperature','humidity','pressure','windspeed','winddirection','sky_brightness',
                  'sky_brightness_timestamp']:
        print(f'\n{datum}:')
        for key in ['Description','Units']:
            print(f"  {key}: {lbtData.attrs[key][datum]}")

lbtMJD = lbtData['time_stamp']*1.0e-6/86400.0 # convert MJD in microseconds to days
lbtMJD0 = int(lbtMJD[0])
lbtHour = 24.0*(lbtMJD-lbtMJD0)
      
t = Time([lbtMJD0], format='mjd', scale='utc')
utcDate = f"{t.to_value('iso',subfmt='date')[0]}"

lbtTemp = lbtData['temperature']
lbtDewP = lbtData['dewpoint']
lbtPres = lbtData['pressure']
lbtRH = lbtData['humidity']
lbtWSf = lbtData['windspeed_front']
lbtWDf = lbtData['winddirection_front']
lbtWSr = lbtData['windspeed']
lbtWDr = lbtData['winddirection']
lbtSky = lbtData['sky_brightness']

lbtEnv.close()

# SMT Environmental Data

haveSMT = True
try:
    smtEnv = hdf.File(smtFile,'r')
except:
    haveSMT = False
    plotPWV = False
    
if haveSMT:
    smtDS = list(smtEnv.keys())[0]
    if verbose:
        print(smtDS)

    smtData = smtEnv[smtDS]

    if verbose:
        print("\nSMT Env Data:")
        print(smtData.dtype) # uncomment to see all data values

        for datum in ['time_stamp','amb_temp','amb_pres','humidity','mm_h2o','tau_0','tauz','tausigma','refract','tipper_az']:
            print(f'\n{datum}:')
            for key in ['Description','Units']:
                print(f"  {key}: {smtData.attrs[key][datum]}")
        
    smtMJD = smtData['time_stamp']*1.0e-6/86400.0 # convert MJD in microseconds to days
    smtMJD0 = int(smtMJD[0])
    smtHour = 24.0*(smtMJD-smtMJD0)

    smtTemp = smtData['amb_temp']
    smtPres = smtData['amb_pres']
    smtRH = smtData['humidity']
    smtPWV = smtData['mm_h2o']
    tau0 = smtData['tau_0']

    smtEnv.close()

i = -1

t = Time(lbtMJD[i], format='mjd', scale='utc')

if verbose:
    print("Last Measurement:")
    print(f"  LBT: {t.to_value('iso')} {lbtTemp[i]:.1f} C {lbtPres[i]:.1f} hPa {lbtRH[i]:.1f}% front={lbtWSf[i]:.1f} m/s rear={lbtWSr[i]:.1f} m/s Sky={lbtSky[i]:.1f} mag")

if haveSMT:
    t = Time(smtMJD[i], format='mjd', scale='utc')
    if verbose:
        print(f"  SMT: {t.to_value('iso')} {smtTemp[i]:.1f} C {smtPres[i]:.1f} hPa {smtRH[i]:.1f}% PWV={smtPWV[i]:.2f}mm tau0={tau0[i]:.2f}")

# plotting limits

# UTC time

if haveSMT:
    minTime = np.min([np.min(lbtHour),np.min(smtHour)])
    maxTime = np.max([np.max(lbtHour),np.max(smtHour)])
else:
    minTime = np.min(lbtHour)
    maxTime = np.max(lbtHour)
    
dT = maxTime - minTime
tMin = minTime # np.floor(minTime) # minTime - 0.05*dT
tMax = maxTime # np.ceil(maxTime+0.01*dT) # maxTime + 0.05*dT

tMin = 0.0
if nightOnly and tMax > endUTC:
     tMax = endUTC

useSun = True

if useSun:
    tMin = 0.0 # np.floor(ssUTC - 1.0)
    tMax = np.ceil(srUTC + 1.0)

# temperature

if plotDewPt:
    minTemp = np.min([np.min(lbtTemp),np.min(lbtDewP)])
else:
    minTemp = np.min(lbtTemp)
    
maxTemp = np.max(lbtTemp)
dTemp = maxTemp - minTemp
minTemp -= 0.1*dTemp
maxTemp += 0.1*dTemp

# pressure

presFloor = 600.0 # hPa floor, less than this is probably missing data

minPres = np.min(lbtPres[np.where(lbtPres>presFloor)])
maxPres = np.max(lbtPres[np.where(lbtPres>presFloor)])
medPres = np.median(lbtPres[np.where(lbtPres>presFloor)])
dP = maxPres - minPres
if dP < 10:
    minPres = medPres - 5.0
    maxPres = medPres + 5.0
else:
    minPres -= 0.05*dP
    maxPres += 0.05*dP
#minPres = 670
#maxPres = 690

# humidity

minRH = np.min(lbtRH)
maxRH = np.max(lbtRH)
minRH = 0
maxRH = 105

# wind speeds

minWS = 0.0 # np.min([np.min(lbtWSf),np.min(lbtWSr)])
maxWS = 1.05* np.max([np.max(lbtWSf),np.max(lbtWSr)])
wsWarning = 20.0 # m/s - gust warning limit
wsLimit = 22.0 # m/s - closing limit
wsSensMax = 40.0 # m/s - fastest speed it can measure (~90m/s)

if maxWS < wsLimit:
    maxWS = wsLimit+5.0
elif maxWS > 35:
    maxWS = wsSensMax
    
# PWV

if haveSMT:
    minPWV = 0.0 # np.min(smtPWV)
    maxPWV = 1.05*np.max(smtPWV)

# running mean of the wind speed.  Sampling is ~1 second so nFilt=60 is about 1 minute rolling mean

nFilt = 300 

smWSf = uniform_filter1d(lbtWSf, size=nFilt)
smWDf = uniform_filter1d(lbtWDf, size=nFilt)

smWSr = uniform_filter1d(lbtWSr, size=nFilt)
smWDr = uniform_filter1d(lbtWDr, size=nFilt)

#----------------------------------------------------------------
#
# Weather data plot
#

# 5 panels if plotting PWV, 4 with just LBT data

if plotPWV:
    fig,(axT,axRH,axWS,axP,axPWV) = plt.subplots(5,1,figsize=(wInches,hInches),dpi=dpi)
else:
    fig,(axT,axRH,axWS,axP) = plt.subplots(4,1,figsize=(wInches,hInches),dpi=dpi)

fig.subplots_adjust(wspace=0, hspace=0.2)

# Top panel - temperature

axT.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
axT.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

axT.set_ylabel(r'Temperature [C]')

axT.xaxis.set_major_locator(MultipleLocator(1.0))
axT.xaxis.set_minor_locator(MultipleLocator(0.5))
axT.set_xlim(tMin,tMax)

#axT.yaxis.set_major_locator(MultipleLocator(5))
#axT.yaxis.set_minor_locator(MultipleLocator(1))
axT.set_ylim(minTemp,maxTemp)

axT.plot(lbtHour,lbtTemp,'-',color='blue',lw=0.5,zorder=10,label='Ambient')

if plotDewPt:
    axT.plot(lbtHour,lbtDewP,'-',color='#ffbf00',lw=0.5,zorder=9,label='Dewpoint')
    axT.legend(fontsize=8,ncol=2)

if plotSun:
    axT.vlines(sstTimes,minTemp,maxTemp,ls=['--'],lw=0.5,colors=['black'],zorder=8)
    for i in range(len(sstTimes)):
        axT.text(sstTimes[i],maxTemp,timeStr[i],va='bottom',ha='center',fontsize=4)
    
axT.set_title(rf'LBT Weather Data {utcDate} UTC')

# second panel - humidity

axRH.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
axRH.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

axRH.set_ylabel(r'Humidity [\%]')

axRH.xaxis.set_major_locator(MultipleLocator(1.0))
axRH.xaxis.set_minor_locator(MultipleLocator(0.5))
axRH.set_xlim(tMin,tMax)

axRH.yaxis.set_major_locator(MultipleLocator(20))
axRH.yaxis.set_minor_locator(MultipleLocator(5))
axRH.set_ylim(minRH,maxRH)
axRH.hlines(90,tMin,tMax,ls=['--'],colors=['#bb0000'],zorder=9,lw=0.5)

axRH.plot(lbtHour,lbtRH,'-',color='blue',lw=0.5)

if plotSun:
    axRH.vlines(sstTimes,minRH,maxRH,ls=['--'],lw=0.5,colors=['black'],zorder=8)

#axRH.plot(smtHour,smtRH,'-',color='green',lw=0.5)

# third panel - wind speeds

axWS.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
axWS.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

axWS.set_ylabel(r'Wind Speed [m/s]')

axWS.xaxis.set_major_locator(MultipleLocator(1.0))
axWS.xaxis.set_minor_locator(MultipleLocator(0.5))
axWS.set_xlim(tMin,tMax)

axWS.yaxis.set_major_locator(MultipleLocator(20))
axWS.yaxis.set_minor_locator(MultipleLocator(5))
axWS.set_ylim(minWS,maxWS)

axWS.plot(lbtHour,lbtWSf,'-',color='blue',lw=0.3,zorder=9,label='Front')
axWS.plot(lbtHour,smWSf,'-',color='cyan',lw=0.3,zorder=10)

axWS.plot(lbtHour,lbtWSr,'-',color='green',lw=0.3,zorder=9,label='Rear')
axWS.plot(lbtHour,smWSr,'-',color='lightgreen',lw=0.3,zorder=10)

axWS.legend(fontsize=6,ncol=4,loc="upper center")

if maxWS > wsLimit:
    axWS.hlines(wsWarning,tMin,tMax,ls=['--'],colors=['#FFBF00'],zorder=10,lw=0.5)
    axWS.hlines(wsLimit,tMin,tMax,ls=['--'],colors=['#FF0000'],zorder=10,lw=0.5)

if plotSun:
    axWS.vlines(sstTimes,minWS,maxWS,ls=['--'],lw=0.5,colors=['black'],zorder=8)

# 4th panel - pressure

axP.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
axP.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')

axP.set_ylabel(r'Pressure [hPa]')

axP.xaxis.set_major_locator(MultipleLocator(1.0))
axP.xaxis.set_minor_locator(MultipleLocator(0.5))
axP.set_xlim(tMin,tMax)

axP.set_ylim(minPres,maxPres)

if not plotPWV:
    axP.set_xlabel(r'UTC Time')

axP.plot(lbtHour,lbtPres,'-',color='blue',lw=0.5,zorder=5)

if plotSun:
    axP.vlines(sstTimes,minPres,maxPres,ls=['--'],lw=0.5,colors=['black'],zorder=8)
    
# bottom - PWV is used if we have SMT data and asked to plot it

if plotPWV:
    axPWV.tick_params('both',length=4,width=lwidth,which='major',direction='in',top='on',right='on')
    axPWV.tick_params('both',length=2,width=lwidth,which='minor',direction='in',top='on',right='on')
    axPWV.set_ylabel(r'PWV [mm]')
    axPWV.xaxis.set_major_locator(MultipleLocator(1.0))
    axPWV.xaxis.set_minor_locator(MultipleLocator(0.5))
    axPWV.set_xlim(tMin,tMax)
    axPWV.set_ylim(minPWV,maxPWV)
    axPWV.set_xlabel(r'UTC Time')
    axPWV.plot(smtHour,smtPWV,'-',color='blue',lw=0.5,zorder=5)

    if plotSun:
        axPWV.vlines(sstTimes,minPWV,maxPWV,ls=['--'],lw=0.5,colors=['black'],zorder=8)

# hardcopy

plt.plot()

plotFile = f'{obsDate}_env.png'
plt.savefig(plotFile,bbox_inches='tight',facecolor='white')

#----------------------------------------------------------------
#
# Wind Rose Plot
#

fig, ax = plt.subplots(subplot_kw={'projection':'polar'},figsize=(wInches,wInches),dpi=dpi)

ax.plot(0,0,'o',ms=2,mfc='blue',mec=None,mew=0,zorder=1,label='Front')
ax.plot(0,0,'o',ms=2,mfc='green',mec=None,mew=0,zorder=1,label='Rear')

if nightOnly:
    iNight = np.where((lbtHour <= endUTC) & (lbtHour >= startUTC))[0]
    WSf = lbtWSf[iNight]
    WDf = lbtWDf[iNight]
    WSr = lbtWSr[iNight]
    WDr = lbtWDr[iNight]
else:
    WSf = lbtWSf
    WDf = lbtWDf
    WSr = lbtWSr
    WDr = lbtWDr

alpha = 0.08/(len(WSf)/1.0e4)
if alpha < 0.01:
    alpha = 0.01
if maxWS == wsSensMax:
    alpha = 0.05

# front anemometer

iSafe = np.where(WSf <= wsWarning)[0]
if len(iSafe) > 0:
    ax.plot(np.radians(WDf[iSafe]),WSf[iSafe],'o',ms=2,mfc='blue',mec=None,mew=0,alpha=alpha,zorder=8)

iWarn = np.where((WSf > wsWarning) & (WSf <= wsLimit))
if len(iWarn) > 0:
    ax.plot(np.radians(WDf[iWarn]),WSf[iWarn],'o',ms=2,mfc='#ffbf00',mec=None,mew=0,alpha=0.25,zorder=10)
    
iMax = np.where((WSf > wsLimit) & (WSf <= wsSensMax))[0]
if len(iMax) > 0:
    ax.plot(np.radians(WDf[iMax]),WSf[iMax],'o',ms=2,mfc='red',mec=None,mew=0,alpha=0.25,zorder=10)

# rear anemometer

iSafe = np.where(WSr <= wsWarning)[0]
if len(iSafe) > 0:
    ax.plot(np.radians(WDr[iSafe]),WSr[iSafe],'o',ms=2,mfc='green',mec=None,mew=0,alpha=alpha,zorder=9)

iWarn = np.where((WSr > wsWarning) & (WSr <= wsLimit))
if len(iWarn) > 0:
    ax.plot(np.radians(WDr[iWarn]),WSr[iWarn],'o',ms=2,mfc='#ffbf00',mec=None,mew=0,alpha=0.25,zorder=10)

iMax = np.where((WSr > wsLimit) & (WSr <= wsSensMax))[0]
if len(iMax) > 0:
    ax.plot(np.radians(WDr[iMax]),WSr[iMax],'o',ms=2,mfc='red',mec=None,mew=0,alpha=0.25,zorder=10)

ax.set_rmax(maxWS)
if maxWS == wsSensMax:
    ax.set_rticks([5,10,15,20,25,30,35,40])
else:
    ax.set_rticks([5,10,15,20,25,30])

ax.set_thetagrids([0,45,90,135,180,225,270,315],['E','NE','N','NW','W','SW','S','SE'])

ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax.grid(True,lw=0.5)
ax.legend(fontsize=6,ncol=4,markerscale=2)

# maximum wind speed limit

ax.plot(np.linspace(0,2.0*np.pi,301),wsLimit*np.ones(301),'--',lw=0.8,zorder=10,color='#bb0000')
ax.plot(np.linspace(0,2.0*np.pi,301),wsWarning*np.ones(301),'--',lw=0.8,zorder=10,color='#ffbf00')

labPA = ax.get_rlabel_position()
ax.text(np.radians(labPA),ax.get_rmax()+1,'wind\nspeed\n[m/s]',rotation=labPA,ha='left',va='center')

ax.set_title(rf'LBT wind speed and direction {utcDate} UTC', va='bottom')

plt.plot()

# hardcopy

plotFile = f'{obsDate}_wind.png'
plt.savefig(plotFile) # ,bbox_inches='tight')#,facecolor='white')

# All Done

print(f"Done: created weather plots for {obsUTC} UTC")
sys.exit(0)
