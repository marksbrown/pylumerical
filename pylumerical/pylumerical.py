"""
 Module : PyLumerical
 Author : Mark S. Brown
 Started : 10th September 2013

 In this module I will collect functions used for :
   + Generating Lumerical script files
   + Processing and analysing output from Lumerical
   + Optimisation routines using custom metrics

"""

from __future__ import print_function, division
import itertools
import os
from subprocess import check_output
import datetime

def writedetails(workingdir, keyword, defaultparams, newparams, verbose=0):
    '''
    Writes important details to text file within directory
    '''
    
    writedatatofile = open(os.path.join(workingdir,keyword,'README'), 'w')
    
    writedatatofile.write("Files generated on {0} at {1}\n".format(datetime.date.today(),datetime.datetime.now()))
    writedatatofile.write("\n--Default parameters--\n")
    for key, value in defaultparams.iteritems():
        writedatatofile.write("{0}={1}\n".format(key,value))
        
    writedatatofile.write("\n--Parameter Sweeping over--\n")
    for name, param in newparams:
        writedatatofile.write("{0} swept from {1} to {2} in {3} steps\n".format(name,min(param),max(param),len(param)))
    
    writedatatofile.close()


def ParameterSweepInput(workingdir, keyword, newparams, defaultparams, script, verbose=0, output_simulation_names=False,delete_existing_files=False,show_created_fsp_files=False):
        
    '''
    Parameter Sweep for FDTD-Solutions

    workingdir : location to place input, fsp and output folders
    keyword : identifier of parameter sweep for you convenience
    newparams : list of parameters (see _GenerateParameterSweepDict_ function) we wish to iterate over
    defaultparmas : default dictionary of every parameter needed
    script : (scriptloc, scriptname) of original FDTD-Solutions lsf script we wish to modify
    execute : should the generated files we executed locally immediately?
    '''
    lsfloc, fsploc, dataloc = SetupEnvironment(workingdir, keyword,verbose=verbose,delete_existing_files=delete_existing_files)

    writedetails(workingdir, keyword, defaultparams, newparams)

    lsffiles = GenerateParameterSweepDictionary(newparams, defaultparams,
                                                verbose=verbose)

    # Display the number of simulations that will be created
    print("Generating "+str(len(lsffiles))+" simulations...")
    # I have added this here as using the main verbose variable outputs too much info
    if output_simulation_names==True:
        for lsfname, parameters in lsffiles:
            print(lsfname)

    for lsfname, parameters in lsffiles:
        if verbose > 0:
            print(lsfname)
        lsf = (lsfloc, lsfname)
        fsp = (fsploc, lsfname)
        GenerateLSFinput(script, lsf, fsp, parameters, verbose=verbose)
        GenerateFSPinput(lsf, verbose=verbose)

        if any([afile.endswith('xml') for afile in os.listdir(lsfloc)]):
            raise ValueError(
                "lsf file : " +
                lsfname +
                " is not correct. Check error in input directory.")

    if show_created_fsp_files:
        print("\nCreated:")
        for created_file in os.listdir(fsploc):
            if created_file.endswith(".fsp"):
                print(created_file)
        print("\n")

    return fsploc, dataloc


def ExecuteFSPfiles(fsploc, cores=8, execute=True, verbose=0):
    '''
    Executes all fsp files in _fsploc_

    TODO - Get code to work properly for a list of lsffiles

    see : http://docs.lumerical.com/en/fdtd/user_guide_run_linux_fdtd_command_line_multi.html
    '''

    ExecFSP = "fdtd-run-local.sh -n " + \
        str(cores) + ' ' + os.path.join(fsploc, "*.fsp")

    if verbose > 0:
        print(ExecFSP)

    if execute:
        return check_output(ExecFSP, shell=True)
    else:
        return ExecFSP

def ExecuteScriptOnFSP(fsp, script, execute=True, verbose=0, **kwargs):
    '''
    All fsp files in _fsploc_ are executed with _scriptname_ from _scriptloc_

    This code can be used to extract raw data from processed simulations
    '''

    fsploc, fspname = fsp
    scriptloc, scriptname = script

    ExecLumerical = kwargs.get('lumerical', 'fdtd-solutions')

    toexec = ExecLumerical + " " + os.path.join(fsploc, fspname) + " -run " +\
        os.path.join(scriptloc, scriptname) + ".lsf -nw"
    if verbose > 0:
        print(toexec)

    if execute:
        return check_output(toexec, shell=True)
    else:
        return toexec


try:
    from fabric.api import run

    def ExecuteFSPfilesRemote(fsploc, loc='tinker.ee.ucl.ac.uk', cores=8, nicelvl=-19, verbose=0):
        '''
        This will execute all the given fsp files on a remote machine using the
        _ExecuteFSPfiles_ command above
        '''

        acmd = "/bin/nice -n {0:.0f} {1}".format(nicelvl,
                                ExecuteFSPfiles(fsploc, cores, execute=False,
                                                verbose=verbose))

        return run(acmd)

except ImportError:
    print("Fabric is not found, ignoring ...")


def ProcessGenerated(fsploc, outputloc, processingloc,
                     processingscript, scriptparams={}, verbose=0):
    '''
    Apply processing script to fsp file that has successfully run through FDTD-solutions
    '''
    for fspname in os.listdir(fsploc):
        if not fspname.endswith("fsp"):
            continue

        if verbose > 0:
            print("Processing", fspname)

        variables = dict(
            {'Savefullpath': os.path.join(outputloc, fspname)}.items() + scriptparams.items())

        if verbose > 0:
            print(variables)

        # cuts off .fsp from filename
        fullpath = os.path.join(fsploc, fspname.split('.')[0])
        tmpscript = (processingloc, 'TemporaryScript')

        AlterVariables(
            (processingloc,
             processingscript),
            tmpscript,
            variables,
            verbose=0)

        fsp = (fsploc, fspname)
        Success = ExecuteScriptOnFSP(fsp, tmpscript, verbose=0)

        if verbose > 0:
            print(fspname, "returns with code", Success)


def SetupEnvironment(workingdir, akeyword, verbose=0,delete_existing_files=False):
    '''
    Creates input, processing and output folders
    '''
    keyword = lambda adir: os.path.join(akeyword, adir)
    lsfloc = full(workingdir, keyword('input'), verbose=verbose)  # input
    fsploc = full(workingdir, keyword('fsp'), verbose=verbose)  # inbetween
    dataloc = full(workingdir, keyword('output'), verbose=verbose)  # output

    if delete_existing_files:
	print("\nDeleting pre-existing .lsf files")                  
        for existing_file in os.listdir(lsfloc):
            os.remove(os.path.join(lsfloc,existing_file))
            print(existing_file," DELETED")
	print("\nDeleting pre-existing .fsp files")                  
        for existing_file in os.listdir(fsploc):
            os.remove(os.path.join(fsploc,existing_file))
            print(existing_file," DELETED")
	print("\nDeleting pre-existing .csv files")                  
        for existing_file in os.listdir(dataloc):
            os.remove(os.path.join(dataloc,existing_file))
            print(existing_file," DELETED")
	print("\n")

    return lsfloc, fsploc, dataloc


def full(workingdir, adir, verbose=0):
    '''
    Gets full directory (creates folder if it doesn't already exist)
    '''

    fullpath = os.path.join(workingdir, adir)

    if not os.path.exists(fullpath):
        os.makedirs(fullpath)

    return fullpath


def GenerateParameterSweepDictionary(newparams, defaultparams, verbose=0):
    '''
    This will return the dictionary ready for insertion into the lsf file
    newparms should have have format [(parameter_name1, values1),(parameter_name2, values2),...]
    '''
    names, parameters = zip(*newparams)
    newparamdict = [dict(zip(names, item))
                    for item in itertools.product(*parameters)]

    return (
        [lsftogenerate(override, defaultparams) for override in newparamdict]
    )


def _uniquedictstring(adict):
    '''
    Turns dictionary into unique name
    '''
    uniquename = "_".join("{0}={1}".format(key, data)
                          for key, data in adict.iteritems())
    return uniquename.replace('.', ',')


def lsftogenerate(newparams, defaultparams):
    '''
    Returns dict of parameters along with unique name determined by given parameters
    '''
    uniquename = _uniquedictstring(newparams)

    newparams = dict(defaultparams.items() + newparams.items())
    return [uniquename, newparams]

# /typecast##
# http://stackoverflow.com/questions/7019283/automatically-type-cast-parameters-in-python


def __boolify(astr):
    '''
    String to Bool
    '''
    if astr == 'True' or astr == 'true':
        return True
    if astr == 'False' or astr == 'false':
        return False
    raise ValueError('Not Boolean Value!')


def estimateType(var):
    '''guesses the str representation of the variables type'''
    var = str(var)  # important if the parameters aren't strings...
    for caster in (__boolify, int, float):
        try:
            return caster(var)
        except ValueError:
            pass
    return var

# /typecast##


def GetCurrentParameters(root, verbose=0, **kwargs):
    '''
    Extracts parameters from Lumerical script file
    when surrounded by <variable> and </variable> tags
    '''
    unwanted = kwargs.get('unwanted', ["\n", ";", "'", "#"])

    rootloc, rootname = root

    params = []
    invar = False
    for i, aline in enumerate(open(os.path.join(rootloc, rootname + '.lsf'), 'r')):
        for achar in unwanted:
            aline = aline.replace(achar, '')
        if verbose > 1:  # prints full output
            print(aline)
        if aline == "<variables>":
            invar = True
            startline = i
            continue
        elif aline == "</variables>":
            return (startline + 1, i), {a: estimateType(b) for a, b in params}
        if invar and aline != "":
            if verbose > 0:
                print(i, ":", aline)
            params.append(aline.split(' = '))


def _GeneratenewLSF(root, lsf, variables, verbose=0):
    '''
    Updates parameters in variable section and returns new file

    If this function is called by the user,  they must close __newlsf__!!
    '''
    rootloc, rootname = root
    lsfloc, lsfname = lsf

    (lmin, lmax), params = GetCurrentParameters(root, verbose=verbose)
    newlsf = open(os.path.join(lsfloc, lsfname + '.lsf'), 'w')
    for i, aline in enumerate(open(os.path.join(rootloc, rootname + '.lsf'), 'r')):
        if i < lmin or i > lmax:  # outside range write original file as usual
            newlsf.write(aline)
            continue

        if verbose > 0:
            print("line : variable : new line")
        for j, akey in enumerate(variables):
            if isinstance(variables[akey], bool):  # Type casts for Lumerical
                aparam = int(variables[akey])
            elif isinstance(variables[akey], str):
                aparam = "'" + variables[akey] + "'"
            elif isinstance(variables[akey], int):
                aparam = int(variables[akey])
            elif isinstance(variables[akey], float):
                aparam = float(variables[akey])
            else:
                if verbose > 0:
                    print("unknown type!", type(variables[akey]))
                aparam = "'" + variables[akey] + "'"
                # TODO make code work properly with python3 unicode

            newline = akey + " = " + str(aparam) + ";\n"
            if verbose > 0:
                print(i, ":", j, ":", newline, end="")
            newlsf.write(newline)
        newlsf.write('#</variables>#\n')

    return newlsf


def AlterVariables(root, lsf, variables, verbose=0):
    '''
    Alter parameters of existing lsf file and add new variables only
    old variables WILL be removed
    '''

    newlsf = _GeneratenewLSF(root, lsf, variables, verbose=verbose)
    newlsf.write("exit(2);\n")
    newlsf.close()


def GenerateLSFinput(root, lsf, fsp, variables, verbose=0):
    '''
    Generates new lsf file in _lsfloc_ with name _lsfname_ using the original
    script file _rootname_ from _rootloc_ with additional _variables_

    When executed it will save the fsp binary (with the same name) into _fsploc_
    '''

    lsfloc, lsfname = lsf
    rootloc, rootname = root
    fsploc, fspname = fsp
    #scriptloc, scriptname = script

    if not os.path.exists(rootloc):
        print("Root location doesn't exist!")
        return

    if not os.path.exists(lsfloc):
        print("lsf location doesn't exist!")
        return

    newlsf = _GeneratenewLSF(root, lsf, variables, verbose=verbose)
    newlsf.write("\ncd('" + fsploc + "');\n")
    newlsf.write("save('" + fspname + "');\n")

#    if len(scriptloc) > 0:
#        print(scriptloc, scriptname)
#        fullloc = os.path.join(scriptloc, scriptname)
#        newlsf.write("if(layoutmode==0){\n")
#        newlsf.write("feval('" + fullloc + "');\n")
#        newlsf.write("}\n")
    newlsf.write("exit(2);\n")
    newlsf.close()


def GenerateFSPinput(lsf, verbose=0, **kwargs):

    lsfloc, lsfname = lsf
    gui = kwargs.get('gui', False)
    run = kwargs.get('run', True)
    logfile = kwargs.get('logfile', False)

    ExecLumerical = kwargs.get('lumerical', 'fdtd-solutions')
    arguments = ""
    if not gui:
        arguments += ' -nw'
    if logfile:
        arguments += ' -logfile logFile'
    if run:
        arguments += ' -run'

    arguments += " " + os.path.join(lsfloc, lsfname + '.lsf')
    ExecLumerical += arguments
    if verbose > 0:
        print("calling :", ExecLumerical)
    
    if execute:
        return check_output(ExecLumerical, shell=True)
    else:
        return ExecLumerical
