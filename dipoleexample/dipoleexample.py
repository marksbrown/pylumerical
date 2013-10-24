from __future__ import division,print_function

import os

##consts
nm = 1e-9

##PyLumerical Setup
import pylumerical as pyl
workingdir = '/tmp/lumerical'
datadir = os.getcwd()
rootloc = pyl.full('originalscripts',datadir,verbose=1) #Lumerical geometry scripts to play with
scriptloc = pyl.full('processingscripts',datadir,verbose=1) #Lumerical scripts to act on processed data
originalscript = (scriptloc,'farfieldsave')
tmpscript = (scriptloc,'Tmp')

##setting up
lsfloc = pyl.full('input',workingdir,verbose=1) #input
fsploc = pyl.full('fsp',workingdir,verbose=1) #inbetween
dataloc = pyl.full('output',workingdir,verbose=1) #output

defaultparams = {'BravaisTheta': 90, 'LX': 100*nm, 'LY': 100*nm, 'MonitorMargin': 50*nm,
                'MarginXY' : 50*nm, 'MarginZ' : 50*nm, 'N01': 0, 'N02': 0, 'N11': 0, 
                'N12': 0, 'MonitorLoc': 0, 'phi': 0,'theta': 0}

customname = lambda params : "_".join(['DipoleArray']+params)
MonitorLocation = {0:'x',2:'y',4:'z'}
lsffiles = []
#/setting up

for N in range(0,11,2): #parameter(s) we're sweeping through
    for aloc in MonitorLocation:
        OverrideThese = {"MonitorLoc":aloc,"N12":N,"N11":N} #NxN array
        newparams = dict(defaultparams.items()+OverrideThese.items())
        
        lsfname = customname([MonitorLocation[aloc],str(N)])
        lsffiles.append(lsfname)
        print("--",lsfname,"--")
        
        root = (rootloc,'DipoleArray')
        lsf = (lsfloc,lsfname)
        fsp = (fsploc,lsfname)
        pyl.GenerateLSFinput(root,lsf,fsp,newparams)

print("Input :: lsf Scripts Generated")        

for anlsf in lsffiles:
    pyl.GenerateFSPinput((lsfloc,anlsf),verbose=0)
    
print("FSP :: fsp binary files Generated")
Success = pyl.ExecuteFSPfiles(fsploc,verbose=0)

print("FSP :: all fsp files completed with signal",Success)

for fspname in os.listdir(fsploc):
    if not fspname.endswith("fsp"):
        continue
    
    ##Generate new script (new save location per fsp file)
    fullpath = os.path.join(fsploc,fspname.split('.')[0])
    variables = {'Monitor' : "PowerMonitor", 'Savefullpath' : os.path.join(dataloc,fspname)}
    pyl.AlterVariables(originalscript,tmpscript,variables,verbose=0)
    
    fsp = (fsploc,fspname)
    Success = pyl.ExecuteScriptOnFSP(fsp,tmpscript,verbose=0)
    
    print(fspname,"returns with code",Success)
    

print("Output csv files generated")
print("Complete!")
