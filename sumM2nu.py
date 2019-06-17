## This script will automatically sum up nutbar results into an M2nu NME
## The nutbar results come from properly executing nuM2nu.py (so do this first)
## In particular, we calculate the decay: (ZI,A) -> (ZK,A) + e + v [fictituous intermediate state] -> (ZF,A) + 2e + 2v, where ZI=Z, ZK=Z+1, and ZF=Z+2
## With: initial (I) -> intermediate (K) -> final (F)
## NOTE: you must add in the relevant $Eshift and $EXP to "the $Eshift/$EXP if-else ladder" below
## all output files are saved in $nucI/$mydir/$outdir, as set below
##  By: Antoine Belley based on sumM2nu.sh from Charlie Payne
##  Copyright (C): 2019

import argparse
import sys
import re
import os
import glob


parser = argparse.ArgumentParser()
parser.add_argument("ZI",     help = "Atomic (proton) number of the initial nucleus (I)", type=int)
parser.add_argument("A",      help = "Mass number of the decay", type=int)
parser.add_argument("mydir",  help = "The directory holding $nutfileK and $nutfileF")
parser.add_argument("neigK",  help = "The number of eigenstates to create for summing over the K excitation energies." , type=int)
parser.add_argument("qf",     help = "The GT quenching factor (some standards are 0.82, 0.77, 0.74), choose 'def' for the default", type=float)
parser.add_argument("chift",  help = "The choice of $Eshift as set below, the options are 'lit' or 'mine', see 'the $Eshift/$EXP if-else ladder' below")
parser.add_argument("-a","--abin", action='store_true', help ="'abin' = run the sum ab-initio style by setting $EXP (below) to 0, if undesired it may be left blank (therefore running with $EXP correction to the s.e.s.)")
args = parser.parse_args()

if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
    imasms = '/global/home/belley/Scripts_decay/'                           # " " " " " " nuqsub.py script lives
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
    imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # " " " " " " nuqsub.py script lives
else:
    print('This cluster is not known')
    print('Add the paths to execute_M2nu.py in this cluster')
    print('Exiting...')
    exit(1)     


sys.path.append(imasms)
from ReadWrite import *
from make_plot import *

chlit = 'lit'
chmine = 'mine'


ZF = args.ZI+2  #Atomic number after the decay
ZK = args.ZI+1  #Atomic number of intermediate state
if ZF > 62:
    print('ERROR 8898: this nucleus is too heavy => extend the ELEM array!')
    print("ZF ="+str(ZF))
    print('Exiting...')
    exit(1)

ELEM =["blank", "h", "he",
      "li", "be", "b",  "c",  "n",  "o", "f",  "ne",
      "na", "mg", "al", "si", "p",  "s", "cl", "ar",
      "k",  "ca", "sc", "ti", "v",  "cr", "mn", "fe", "co", "ni", "cu", "zn", "ga", "ge", "as", "se", "br", "kr",
      "rb", "sr", "y",  "zr", "nb", "mo", "tc", "ru", "rh", "pd", "ag", "cd", "in", "sn", "sb", "te", "i",  "xe",
      "cs", "ba", "la", "ce", "pr", "nd", "pm", "sm"] # an array of elements from Hydrogen (Z=1) to Samarium (Z=62), includes all current 0vbb candidates

nucI=ELEM[args.ZI]+str(args.A)
nucF=ELEM[ZF]+str(args.A)
nucK=ELEM[ZK]+str(args.A)

#Eshift/EXP if-else ladder. Takes the form:
"""
if nucK == 'example':
    if args.chift == chlit:
        Eshift = 10.000000000 (= M_K + (M_I + M_F)/2 [MeV], the literature concention is ambiguous imo...)
    elif args.chift == chmine:
        Eshift=9.489001054   (= M_K - m_e + (M_I + M_F)/2 [MeV], where these atomic masses are electrically neutral and in the nuclear ground state)
    EXP=9.9999 # the experimental energy between the lowest lying summed excitation state and the ground state for $nucK
"""
if nucK == "sc48":
    if args.chift == chlit:
        Eshift = 1.859700017  # = M_sc48 + (M_ca48 + M_ti48)/2 [MeV]
    elif args.chift == chmine:
        Eshift=1.348701071  # = M_sc48 - m_e + (M_ca48 + M_ti48)/2 [MeV]
    EXP = 2.5173 # the experimental energy between the lowest lying 1+ state and the ground state for sc48
else:
    print("ERROR: the Eshift/EXP for this decay has not been set, please add them to the Eshift/EXP if-else ladder")
    print("nucK = "+nucK)
    print("Exiting...")
    exit(1)


mydir = args.mydir
if mydir.endswith("/"):
    mydir = mydir[:-len("/")]
mydir_MEC = mydir+'_MEC'
argum = mydir.split("_")
maxK  = argum[8]
maxK  = int(re.sub('neig','',maxK))
emax  = argum[6]
flow  = argum[1]
INT   = argum[4]

neigK = args.neigK
if neigK >= maxK :
    neigK = maxK
qf = args.qf
if args.abin:
    abinopt = 'abin'
    EXP = 0
else:
    abinopt = 'corrected'

print('~~~~~~~~~~~~~~~~~~~~~~~~~')
print("A         =  "+str(args.A))
print("nucI      =  "+nucI)
print("nucK      =  "+nucK)
print("nucF      =  "+nucF)
print('~~~~~~~~~~~~~~~~~~~~~~~~~')
print("Eshift    =  "+str(Eshift))
print("EXP       =  "+str(EXP))
print("neigK     =  "+str(neigK))
print("qf        =  "+str(qf))
print("chift     =  "+str(args.chift))
print("abinopt   =  "+abinopt)
print('~~~~~~~~~~~~~~~~~~~~~~~~~')
print("maxK      =  "+str(maxK))
print("flow      =  "+str(flow))
print("int       =  "+str(INT))
print('~~~~~~~~~~~~~~~~~~~~~~~~~')

incheck = input("Is this input acceptable: ")
print("")

if incheck == 'n' or incheck == 'N':
    print("Exiting ...")
    exit(1)

if args.chift != chlit and args.chift != chmine:
    print('ERROR: invalid choice for chift')
    print('chift ='+args.chift)
    print('Exiting...')
    exit(1)

#Make sure those are the same then in goM2nu.py
KIdir    = 'KI_nutbar'
FKdir    = 'FK_nutbar'
nudirI   = 'nushxI_data'
nudirKgs = 'gs_nushxK_data'
nudirK   = 'nushxK_data'
nudirF   = 'nushxF_data'
nutfileK  = "nutbar_tensor1_"+nucK+"0_"+nucI+"0.dat"
nutfileF  = "nutbar_tensor1_"+nucF+"0_"+nucK+"0.dat"

outdir = 'sumM2nu_output' # this is the directory where I'll hold all the output, plotting files, etc...
if args.chift == chlit:
    outdir = outdir+"_"+chlit
elif args.chift == chmine:
    outdir = outdir+"_"+chmine
outdir = outdir+"_"+abinopt


stampL = str(INT)+'_qf'+str(qf)+'_neig'+str(neigK)
stampS = str(INT)+'_neig'+str(neigK)
outfile = outdir+'/M2nu_'+stampL+'.txt' # this will hold the results of the calculations done in this script


os.chdir(nucI+"/"+mydir)
try:
    str(glob.glob(KIdir+"/"+nutfileK)[0])
except IndexError:
    print('ERROR: Cannot find '+nucK+' nutbar files')
    print('mydir    = '+mydir)
    print('KIdir    = '+KIdir)
    print('nutfileK = '+nutfileK)
    print('Exiting...')
    exit(1)

try:
    str(glob.glob(FKdir+"/"+nutfileF)[0])
except IndexError:
    print('ERROR: Cannot find '+nucF+' nutbar files')
    print('mydir    = '+mydir)
    print('FKdir    = '+FKdir)
    print('nutfileF = '+nutfileF)
    print('Exiting...')
    exit(1)

os.makedirs(outdir, exist_ok=True)
os.chdir('../'+mydir_MEC)
os.makedirs(outdir, exist_ok=True)
os.chdir('../'+mydir)


# check to see that $nucfileK and $nucfileF have the same number of lines; they should!
with open(KIdir+'/'+nutfileK,'r') as f1:
    linesK = f1.readlines()
    maxlK = len(linesK)
with open(FKdir+'/'+nutfileF,'r') as f2:
    linesF = f2.readlines()
    maxlF = len(linesF)
if maxlK != maxlF:
    print(nutfileK+" and "+nutfileF+" have different nubers of lines?!")
    print("EXiting...")
    exit(1)


print('Calculating M2nu sum...')
print('Calculating M2nu sum for MEC...')
try:
    M2nu, qM2nu, nmeKI, nmeFK, M2nu_MEC, qM2nu_MEC, nmeKI_MEC, nmeFK_MEC,  ExC = sum_M2nu(mydir = mydir, nucI = nucI, nucK = nucK, nucF = nucF, 
                                                                                 nudirKgs = nudirKgs, KIdir = KIdir, FKdir = FKdir,
                                                                                 neigK = neigK, Eshift= Eshift, EXP = EXP, 
                                                                                 qf = args.qf, abinopt = abinopt)
except:
    M2nu, qM2nu, nmeKI, nmeFK, ExC = sum_M2nu(mydir = mydir, nucI = nucI, nucK = nucK, nucF = nucF, 
                                                                                 nudirKgs = nudirKgs, KIdir = KIdir, FKdir = FKdir,
                                                                                 neigK = neigK, Eshift= Eshift, EXP = EXP, 
                                                                                 qf = args.qf, abinopt = abinopt)
os.chdir('..')


print('Results without MEC:\n')
write_outputfile(outfile, args.A, nucI, nucK, nucF, mydir,
              nudirI, nudirKgs, nudirF, KIdir, FKdir, outdir,
              args.neigK, Eshift, EXP, args.qf, abinopt, 
              M2nu, qM2nu, nmeKI, nmeFK, ExC)
print('Results with MEC:\n')
write_outputfile(outfile, args.A, nucI, nucK, nucF, mydir_MEC,
              nudirI, nudirKgs, nudirF, KIdir, FKdir, outdir,
              args.neigK, Eshift, EXP, args.qf, abinopt, 
              M2nu_MEC, qM2nu_MEC, nmeKI_MEC, nmeFK_MEC, ExC)


make_plot(nucI, args.chift, abinopt, mydir, mydir_MEC, args.qf, outdir,emax)







