####
# DipoleArray Parameter Sweep Example
####

from __future__ import division,print_function
import os
import pylumerical as pyl
from numpy import linspace

##consts
nm = 1e-9

workingdir = '/tmp/lumerical'
scriptloc = os.path.join(os.getcwd(),'originalscripts')
processingloc = os.path.join(os.getcwd(),'processingscripts')

defaultparams = {'BravaisTheta': 90, 'LX': 100*nm, 'LY': 100*nm, 'MonitorMargin': 2*nm,
                'MarginXY' : 200*nm, 'MarginZ' : 100*nm, 'N01': 0, 'N02': 0, 'N11': 0, 
                'N12': 0, 'MonitorLoc': 0, 'phi': 0,'theta': 0}

newparams = [('MonitorLoc' , [2]),
             ('MarginXY' , linspace(100,200,4)*nm)]

fsploc, outputloc = pyl.ParameterSweepInput(workingdir, 'MarginVary', newparams,
                     defaultparams, (scriptloc, 'DipoleArray'), verbose=0)

print("Input lsf & FSP Generated")

pyl.ExecuteFSPfiles(fsploc, cores=8, verbose=0)
print("FSP Processed")

scriptparams = {'Monitor' : "PowerMonitor"}
pyl.ProcessGenerated(fsploc, outputloc, processingloc, 'farfieldsave', scriptparams, verbose=1)
print("Complete!")


