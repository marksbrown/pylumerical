pylumerical
===========

Last Altered : 6th February 2014

Python module to perform tasks with Lumerical FDTD-Solutions

Outline
-------

Pylumerical is a a Python module to alter and execute _Lumerical_ lsf scripts. The code can :

1. Generate multiple _.fsp_ Lumerical binary files from single Lumerical _.lsf_ script file using the GUI licence to perform parameter sweeps.
2. Execute valid _.fsp_ files using Engine licence(s) using MPI.
3. Execute processing _.lsf_ scripts upon completed simulation _.fsp_ files

Original lsf Structure
----------------------
First we need to design a simulation using FDTD-Solutions. The script file should take the form :

```
    deleteall;
    #Description of simulation
    
    #<variables>#
    ...
    #</variables>#
    
    redrawoff;
    
    <Insert simulation definition here>
    
    redrawon;
    
```
Any variables which define the simulation should be placed between the tags. The deleteall command ensures a clean environment before generation. _redrawoff_ and _redrawon_ dramatically speed up the fsp generation time as the GUI is not wasting time drawing the 3D simulation.

Processing lsf Structure
------------------------

```
    #Description of processing script
    #<variables>#
    ...
    #</variables>#

    system("rm -f "+Savefullpath+"*"); #clears output directory

    if(layoutmode==0){

        <Processing Script Details Here!>

        }else{
    ?"No data to analysis in this fsp file!";
    }
    exit(2);
```

In this we've chosen to always output csv files to _SaveFullpath_ which will be added to the processing script automatically.


Parameter Sweep Example
-----------------------

```python
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


import pylumerical as pyl
nm = 1e-9
```
