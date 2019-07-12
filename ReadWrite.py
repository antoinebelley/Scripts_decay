import os
import stat
import glob


#Writes the ans file for nushell and compile it sending the output to the ans.o file

def write_ans(nucleus, neig, sp, inte, Z, A, minJ, maxJ, delJ, parity):
    nucans = nucleus+'.ans'
    nucao  = nucans+'.o'
    f = open(nucans,"w") #Wil overwrite file if they already exists
    f.write('--------------------------------------------------\n')
    f.write("lpe,   "+str(neig)+"             ! option (lpe or lan), neig (zero=10)\n")
    f.write(sp+"                ! model space (*.sp) name (a8)\n")
    f.write('n                    ! any restrictions (y/n)\n')
    f.write(inte+"                ! model space (*.int) name (a8)\n")
    f.write(" "+str(Z)+"                  ! number of protons\n")
    f.write(" "+str(A)+"                  ! number of nucleons\n")
    f.write(" "+str(minJ)+".0, "+str(maxJ)+".0, "+str(delJ)+".0,      ! min J, max J, del J\n")
    f.write('  '+str(parity)+'                  ! parity (0 for +) (1 for -) (2 for both)\n')
    f.write('--------------------------------------------------\n')
    f.write('st                   ! option\n')
    f.close()
    print("Setting up "+ nucans+" for nushellx...")
    os.system("shell "+ nucans+" >> "+nucao) # set up files for nushellx, and divert stdout to file
    st = os.stat(nucleus+'.bat')
    os.chmod(nucleus+'.bat',st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )


def write_nutrunin(nucI, nucF, sp, onebop, twobop, JI=0, NI=1, JF=0, NF=1):
    nutrun   = "nutbar_"+nucF+"0" 
    nutrunin = nutrun+".input"
    f = open(nutrunin,"w")
    f.write(sp+"\n")
    if len(nucI)==3:
        nucIsplit = list(nucI)
        nucI = nucIsplit[0]+'_'+nucIsplit[1]+nucIsplit[2]
    if len(nucF)==3:
        nucFsplit = list(nucF)
        nucF = nucFsplit[0]+'_'+nucFsplit[1]+nucFsplit[2]
    f.write(nucI+"0\n")
    f.write(nucF+"0\n")
    f.write(onebop+' '+twobop+'\n')
    f.write(str(JI)+".0\n")
    f.write(str(NI)+"\n")
    f.write(str(JF)+".0\n")
    f.write(str(NF)+"\n")
    f.write('\n')
    f.close()


def write_sh_M0nu(nushon, nucI, nucF, GTbar, Fbar, Tbar, mydir):
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
        file = "/global/home/belley/Scripts_decay/execute_M0nu.py"
        sh   = "/global/home/belley/Scripts_decay/execute_M0nu.sh"
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        file = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M0nu.py'
        sh   = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M0nu.sh'
    else:
        print('This cluster is not known')
        print('Add the paths to execute_M2nu.py in this cluster')
        print('Exiting...')
        exit(1)     
    f = open(sh, "w")
    f.write('#!/bin/bash\n\n')
    f.write('chmod +x '+file+'\n')
    f.write('python '+file+' '+nushon+' '+nucI+' '+nucF+' '+GTbar+' '+Fbar+' '+Tbar+' '+mydir)
    f.close()
    st = os.stat(sh)
    os.chmod(sh,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )
    return sh


def write_sh_M2nu(srun, nucI, nucK, nucF,mydir):
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
        file = "/global/home/belley/Scripts_decay/execute_M2nu.py"
        sh   = "/global/home/belley/Scripts_decay/execute_M2nu.sh"
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        file = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M2nu.py'
        sh   = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M2nu.sh'
    else:
        print('This cluster is not known')
        print('Add the paths to execute_M2nu.py in this cluster')
        print('Exiting...')
        exit(1)     
    f = open(sh, "w")
    f.write('#!/bin/bash\n\n')
    f.write('chmod +x '+file+'\n')
    f.write('python '+file+' '+srun+' '+nucI+' '+nucK+' '+nucF+' '+mydir)
    f.close()
    st = os.stat(sh)
    os.chmod(sh,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )
    return sh


# function prototype: this function will get the lnum-th line of a file
def getline(lnum, file):
    with open(file, 'r') as f:
        lines = f.readlines()
    return lines[lnum]


# function prototype: this function will get the place-th of a space separated string (aka: vector)
# make sure to put double qoutes around "vector", place counting starts from 0 (not 1)
def getp(vector, place):
    words = vector.split()
    return words[place]


#Verify that the nutbar files exists
def nutbar_exist(nucleus, directory, nutdir, file):
    try:
        path = str(glob.glob(f'{directory}/{nutdir}/{file}')[0])
        return path
    except IndexError:
        print('ERROR: Cannot find '+nucleus+' nutbar files')
        print('directory   = '+directory)
        print('nutdir       = '+nutdir)
        print('nutfileK    = '+file)
        print('Exiting...')
        exit(1)

#Verify that the nutbar have the same number of lines
def verify_nutbar(nucK, nucF, directory, KIdir, FKdir, nutfileK, nutfileF):
    pathK = nutbar_exist(nucK, directory, KIdir, nutfileK)
    pathF = nutbar_exist(nucF, directory, FKdir, nutfileF)
    with open(pathK,'r') as f1:
        linesK = f1.readlines()
        maxlK = len(linesK)
    with open(pathF,'r') as f2:
        linesF = f2.readlines()
        maxlF = len(linesF)
    if maxlK != maxlF:
        print(f'{nutfileK} and {nutfileF} have different nubers of lines in {directory}?!')
        print('Exiting...')
        exit(1)

#Reads ground state energy from the lpt output of nushellx
def read_Egs(nucleus, directory):
    file = nucleus+"*.lpt"
    if len(glob.glob(directory+"/"+file)) == 1 :
        file = glob.glob(directory+"/"+file)[0]
    else:
        print('More than one lpt file!')
        print('Exiting...')
        exit(1)
    Egs = getline(6, file)
    Egs = float(getp(Egs, 2))
    return Egs


#reads the energy for excited states from the lpt output of nushellx
def read_Eses(state, directory, file):
    line = getline(state,directory+"/"+file)
    Eses = float(getp(line, 4))
    nme  = float(getp(line, 8))
    return Eses, nme


def single_M2nu(nmeKI, nmeFK, M2nu, denom):
    numer   = nmeFK*nmeKI                       # numerator of the sum
    tempval = numer/denom                       # see line below
    M2nu    += tempval                             # the M2nu partial sums
    return  M2nu


def getEXP(chift,nucK):
    #Eshift/EXP if-else ladder. Takes the form:
    '''
    if nucK == 'example':
        if args.chift == chlit:
            Eshift = 10.000000000 (= M_K + (M_I + M_F)/2 [MeV], the literature concention is ambiguous imo...)
        elif args.chift == chmine:
            Eshift=9.489001054   (= M_K - m_e + (M_I + M_F)/2 [MeV], where these atomic masses are electrically neutral and in the nuclear ground state)
        EXP=9.9999 # the experimental energy between the lowest lying summed excitation state and the ground state for $nucK
    '''
    if nucK == 'sc48':
        if chift == 'lit':
            Eshift = 1.859700017  # = M_sc48 + (M_ca48 + M_ti48)/2 [MeV]
        elif chift == 'mine':
            Eshift=1.348701071  # = M_sc48 - m_e + (M_ca48 + M_ti48)/2 [MeV] and the 
        EXP = 2.5173 # the experimental energy between the lowest lying 1+ stateground state for sc48
        return EXP, Eshift
    else:
        print('ERROR: the Eshift/EXP for this decay has not been set, please add them to the Eshift/EXP if-else ladder')
        print(f'nucK = {nucK}')
        print('Exiting...')
        exit(1)
