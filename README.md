pylumerical
===========

Python module to work with FDTD software - Lumerical.

Outline
-------

A python wrapper to alter and execute _Lumerical_ scripts is presented. This code will have the following uses :

1. Generate _.fsp_ Lumerical binary files from Lumerical _.lsf_ script files.
2. Execute one (or more) _.fsp_ files with Lumerical's _runparallel;_ option; Allowing Lumerical to automatically load balance across multiple processors and PCs
3. Save and generate _.csv_ files of FarField data. These will be loaded together allowing analysis using Python
4. **Crucially** we can combine the above three features to designate custom metrics along with an optimisation routine to explore parameter space effectively.

Usage
-----
First we need to design a simulation using Lumerical. This should take the form :

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
See http://docs.lumerical.com/en/fdtd/knowledge_base.html for many examples of simulations. See _DipoleArray_ code for an example of the above. _redrawoff;_ and _redrawon;_ are VERY much required - Generation of _fsp_ files will be extremely slow without this.

Parameter Sweep Example
-----------------------

```python
import pylumerical as pyl
nm = 1e-9

datadir = '<LOCATION>/Lumerical/' #where all python and main lumerical scripts live

rootloc = pyl.full('originalscripts',datadir,verbose=1) #Lumerical geometry scripts to play with
scriptloc = pyl.full('processingscripts',datadir,verbose=1) #Lumerical scripts to act on processed data
scriptname = 'farfieldsave' #script to act upon processed data

workingdir = '<ANOTHER LOCATION>/lumerical' #where all generated lsf, fsp and csv files live - potentially ALOT of data!

##setting up
lsfloc = pyl.full('input/NVary',workingdir,verbose=1) #input
fsploc = pyl.full('fsp/NVary',workingdir,verbose=1) #inbetween
dataloc = pyl.full('output/NVary',workingdir,verbose=1) #output
   
#Default parameters of simulation stored as dictionary
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
        #new parameters will override any default parameters we choose
        
        #Lumerical WILL truncate floats - be careful naming files
        lsfname = customname([MonitorLocation[aloc],str(int(N))]) 
        lsffiles.append(lsfname)
        print("--",lsfname,"--")
        
        root = (rootloc,'DipoleArray') #the Lumerical script we've generated beforehand
        lsf = (lsfloc,lsfname)
        fsp = (fsploc,lsfname)
        pyl.GenerateLSFinput(root,lsf,fsp,newparams) #generates all the lsf files for the parameter sweep

print("Input :: lsf Scripts Generated")        

for anlsf in lsffiles:
    pyl.GenerateFSPinput((lsfloc,anlsf),verbose=0) #generates all the fsp files - requires GUI license of Lumerical
    
print("FSP :: fsp binary files Generated")
Success = pyl.ExecuteFSPfiles(fsploc,cores=8,verbose=0) #executes all fsp files in a given directory
#See : http://docs.lumerical.com/en/fdtd/user_guide_run_linux_fdtd_command_line_multi.html

print("FSP :: all fsp files completed with signal",Success)

for fspname in os.listdir(fsploc):
    if not fspname.endswith("fsp"): #skips log files we generate by default (can be turned off in GenerateFSPinput)
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

```
