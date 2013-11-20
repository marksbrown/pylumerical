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
import os


def SetupEnvironment(workingdir, akeyword, verbose=0):
    '''
    Creates input, processing and output folders
    '''
    keyword = lambda adir : os.path.join(adir,akeyword)
    lsfloc = full(keyword('input'),workingdir,verbose=verbose) #input
    fsploc = full(keyword('fsp'),workingdir,verbose=verbose) #inbetween
    dataloc = full(keyword('output'),workingdir,verbose=verbose) #output
    
    return lsfloc, fsploc, dataloc

def lsftogenerate(newparams, defaultparams, sep='-'):
    '''
    Returns dict of parameters along with unique name determined by given parameters
    '''
    uniquename = ""
    for key in newparams:
        uniquename+="_".join([str(key),str(newparams[key])])+sep
    
    newparams = dict(defaultparams.items()+newparams.items())
    return [uniquename, newparams]

def full(adir, workingdir, verbose=0):
    '''
    Gets full directory (creates folder if it doesn't already exist)
    '''

    fullpath = os.path.join(workingdir, adir)
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)        
    
    return fullpath

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


def __GeneratenewLSF(root, lsf, variables, verbose=0):
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
                    print("unknown type!",type(variables[akey]))
                aparam = "'" + variables[akey] + "'"
                ##TODO make code work properly with python3 unicode

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

    newlsf = __GeneratenewLSF(root, lsf, variables, verbose=verbose)
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

    newlsf = __GeneratenewLSF(root, lsf, variables, verbose=verbose)
    newlsf.write("cd('" + fsploc + "');\n")
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

    return os.system(ExecLumerical)


def ExecuteFSPfiles(fsploc, cores=8, verbose=0):
    '''
    Executes all fsp files in _fsploc_

    TODO - Get code to work properly for a list of lsffiles

    see : http://docs.lumerical.com/en/fdtd/user_guide_run_linux_fdtd_command_line_multi.html
    '''


    ExecFSP = "fdtd-run-local.sh -n " + \
        str(cores) + ' ' + os.path.join(fsploc, "*.fsp")

    if verbose > 0:
        print(ExecFSP)

    return os.system(ExecFSP)


def ExecuteScriptOnFSP(fsp, script, verbose=0, **kwargs):
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

    return os.system(toexec)
