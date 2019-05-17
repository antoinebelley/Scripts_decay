## This script will automatically sum up nutbar results into an M2nu NME
## The nutbar results come from properly executing nuM2nu.py (so do this first)
## In particular, we calculate the decay: (ZI,A) -> (ZK,A) + e + v [fictituous intermediate state] -> (ZF,A) + 2e + 2v, where ZI=Z, ZK=Z+1, and ZF=Z+2
## With: initial (I) -> intermediate (K) -> final (F)
## NOTE: you must add in the relevant $Eshift and $EXP to "the $Eshift/$EXP if-else ladder" below
## all output files are saved in $nucI/$mydir/$outdir, as set below
##  By: Antoine Belley based on sumM2nu.sh from Charlie Payne
##  Copyright (C): 2019

import argparse
import re
import os
import glob

parser = argparse.ArgumentParser()
parser.add_argument("ZI",     help = "Atomic (proton) number of the initial nucleus (I)", type=int)
parser.add_argument("A",      help = "Mass number of the decay", type=int)
parser.add_argument("mydir",   help = "The directory holding $nutfileK and $nutfileF")
parser.add_argument("neigK",  help = "The number of eigenstates to create for summing over the K excitation energies. Choose max for maximum.")
parser.add_argument("qf",     help = "The GT quenching factor (some standards are 0.82, 0.77, 0.74), choose 'def' for the default")
parser.add_argument("chift",  help = "The choice of $Eshift as set below, the options are 'lit' or 'mine', see 'the $Eshift/$EXP if-else ladder' below")
parser.add_argument("-a","--abin", action='store_true', help ="'abin' = run the sum ab-initio style by setting $EXP (below) to 0, if undesired it may be left blank (therefore running with $EXP correction to the s.e.s.)")
args = parser.parse_args()

precision = 12      # the bc decimal precision
abinon = 'abin'
chlit = 'lit'
chmine = 'mine'


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

Eshift=0  # initialize the energy shift in the demoninator of the M2nu NME summation equation [MeV]
EXP=0     # initialize the experimental energy correction (between the lowest lying summed ecxited state and the ground state for the K nucleus) [MeV]


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
argum = mydir.split("_")
maxK = argum[8]
maxK = re.sub('neig','',maxK)
flow = argum[1]
INT  = argum[4]

neigK = args.neigK
if neigK >= 'max' :
    neigK = maxK
qf = args.qf
if qf == 'def':
    qf =0.77
qfp = int(qf*100)
if args.abin:
    abinopt = 'corrected'
    EXP = 'off'
else:
    abinopt = 'default'

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

#Make sure those respect the naming convention used in mydir
KIdir    = 'KI_nutbar'      
FKdir    = 'FK_nutbar'       
nutfileK  = "nutbar_tensor0_"+nucK+"0.dat"
nutfileF  = "nutbar_tensor0_"+nucF+"0.dat"

os.chdir(nucI+"/"+mydir)

try:
    nutfileK_path = str(glob.glob(KIdir+"/"+nutfileK)[0])
except IndexError:
    print('ERROR: Cannot find '+nucK+' nutbar files')
    print('mydir    = '+mydir)
    print('KIdir    = '+KIdir)
    print('nutfileK = '+nutfileK)
    print('Exiting...')
    exit(1)

try:
    nutfileF_path = str(glob.glob(FKdir+"/"+nutfileF)[0])
except IndexError:
    print('ERROR: Cannot find '+nucF+' nutbar files')
    print('mydir    = '+mydir)
    print('FKdir    = '+FKdir)
    print('nutfileF = '+nutfileF)
    print('Exiting...')
    exit(1)

outdir = 'sumM2nu_output' # this is the directory where I'll hold all the output, plotting files, etc...
if args.chift == chlit:
    outdir = outdir+"_"+chlit
elif args.chift == chmine:
    outdir = outdir+"_"+chmine
outdir = outdir+"_"+abinopt

os.makedirs(outdir, exists_ok=True)

stampL = INT+'_qf'+qfp+'_nieg'+neigK
stampS = INT+'_neig'+neigK

outfile = 'M2nu_'+stampL+'.txt' # this will hold the results of the calculations done in this scrip
f = open(outfile, 'w')
f.write("mydir         =  "+mydir+"\n")
f.write("A             =  "+str(args.A)+"\n")
f.write("nucI          =  "+nucI+"\n")
f.write("nucK          =  "+nucK+"\n")
f.write("nucF          =  "+nucF+"\n")
f.write("Eshift        =  "+str(Eshift)+"\n")
f.write("EXP           =  "+str(EXP)+"\n")
f.write("qf            =  "+str(qf)+"\n")
f.write("abinopt       =  "+abinopt+"\n")

# get the nuclear g.s. energies

#make sure those are the same then in goM2nu.py
nudirI   = 'nushxI_data'     
nudirKgs = 'gs_nushxK_data'   
nudirK   = 'nushxK_data'     
nudirF   = 'nushxF_data' 

fileKgs  = nucK+"*.lpt"
EKgs     = getline(7, nudirKgs+"/"+fileKgs)
EKgs     = getp(EKgs, 2)
fileIgs  = nucI+"*.lpt"
EIgs     = getline(7, nudirI+"/"+fileIgs)
EIgs     = getp(EIgs, 2)
fileFgs  = nucF+"*.lpt"
EFgs     = getline(7, nudirF+"/"+fileFgs)

f.write("EIgs          =  "+str(EIgs)+"\n")
f.write("EKgs          =  "+str(EIgs)+"\n")
f.write("EFgs          =  "+str(EIgs)+"\n")

# check to see that $nucfileK and $nucfileF have the same number of lines; they should!
with open(KIdir+'/'+nutfileK,'r') as f:
    linesK = f.readlines()
    maxlK = len(linesK)
with open(FKdir+'/'+nutfileF,'r') as f:
    linesF = f.readlines()
    maxlF = len(linesF)

if maxlK != maxlF:
    print(nutfileK+" and "+nutfileF+" have different line conts?!")
    print("EXiting...")
    exit(1)

# make a plotting scripts with accompanying data, which will be filled during the summation below
mhplot     = 'Fig1MH'
myplot     = 'Fig2CP'
plotfileuq = "uq"+mhplot+"_"+stampL+".dat"     # this file will hold what is needed to plot something similar to FIG. 1 of PRC.75.034303(2007)
plotfileq  = "q"+mhplot+"_"+stampL+".dat"      # this file will hold what is needed to plot something similar to FIG. 1 of PRC.75.034303(2007)
plotsh1    = "plot"+mhplot+"_"+stampL+".plt"   # this file will plot the above, in $outdir use the command: gnuplot $plotsh1
plotfileKI = "KIplot_"+stampS+".dat"           # this file is for plotting the nmeKI vs Ex, as set below
plotfileFK = "FKplot_"+stampS+".dat"           # " " " " " " nmeFI " ", " " "
plotsh2    = "plot"+myplot+"_"+stampS+".plt"    # this file will plot the above, in $outdir use the command: gnuplot $plotsh2
f.write("plotfileuq    =  "+plotfileuq+"\n")
f.write("plotfileq     =  "+plotfileq+"\n")
f.write("plotfsh1      =  "+plotsh1+"\n")
f.write("plotfileKI    =  "+plotfileKI+"\n")
f.write("plotfileFK    =  "+plotfileFK+"\n")
f.write("plotsh2       =  "+plotsh2+"\n")



p1 = open(plotsh1,"w")
p1.write("set terminal png\n")
p1.write("set output "+mhplot+"_"+INT+".png")
if flow == 'BARE':
    p1.write('set xrange [0:15]')
    p1.write('set yrange [0:0.12]')
p1.write("plot '"+plotfileq+"' w l title 'qf ="+qf+"', \\\n")
p1.write("     '"+plotfileuq+"' w l 'qf = 1'\n")
p1.close()


p2 = open(plotsh2,"w")
p2.write("set terminal png\n")
p2.write("set output "+mhplot+"_"+INT+".png")
if flow == 'BARE':
    p2.write('set xrange [2:15]')
    p2.write('set arrow form 2,0 to 15,0 nohead linetype 9\n')
else:
    p2.write('set arrow form 0,0 to 30,0 nohead linetype 9\n')
p2.write("     '"+plotfileKI+"' w l '< K | \\sigma\\tau | I >'\n")
p2.write("     '"+plotfileFK+"' w l '< F | \\sigma\\tau | K >'\n")
p2.close()


# preform the sum that defines M2nu, that is:
# M^{2\nu} = \sum_K [ < F | \sigma\tau | K > < K | \sigma\tau | I > / ( E_K - E_\text{gs} + $Eshift ) ]
print('Calculating M2nu sum...')
f.write("nmeFK\t\t*\tnmeKI\t\t->\tnumer\t\t|  EK       EKgs     ; EK-EKgs +  Cexp   +  Eshift       ->  denom\t\t|\tnumer/denom\t+=  M2nu [running sum]")
f.write("----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")


M2nu = 0 # initialize the sum over K
Cexp = 0 # initialize the correction value = $EXP - min($EK-$EKgs)
maxKsum=neigK+8-1
peuq = open(plotfileuq,"w")
peq  = open(plotfileq,"w")
pKI  = open(plotfileKI,"w")
pFK  = open(plotfileKI,"w")
for i in range(8,maxKsum+1):
    lineK   = getline(i,KIdir+"/"+nutfileK)
    EK      = float(getp(lineK, 4))
    nmeKI   = float(getp(lineK, 8))
    lineF   = getline(i, FKdir+"/"+nutfileF)
    EF      = float(getp(lineF, 4))
    nmeFK   = float(getp(lineF ,8))             
    numer   = nmeFK*nmeKI                       # numerator of the sum
    Ex      = EK-EKgs                           # the excitation energy     
    if args.EXP != 'off' and i == 8:
        Cexp = EXP - Ex                         # the experimental energy correction value
    ExC     = Ex+Cexp                           # the (experimentally corrected) excitation energy
    denom   = Ex +Cexp+Eshift                   # denominator of the sum
    tempval = numer/denom                       # see line below
    M2nu    += tempval                          # the M2nu partial sums
    qM2nu   = M2nu *qf*qf                       # the quenched version of M2nu, it has two factors of qf since there are two GT operators in the numerator
    aM2nu   = abs(M2nu)                         # just for plotting the partial sums
    aqM2nu  = abs(qM2nu)                        # just for plotting the quenched partial sums
    peuq.write(ExC+"\t"+aM2nu+"\n")
    peq.write(ExC+"\t"+aqM2nu+"\n")
    pKI.write(ExC+"\t"+nmeKI+"\n")
    pFK.write(ExC+"\t"+nmeFK+"\n")
    f.write(nmeFK+"\t*\t"+nmeKI+"\t->\t"+numer+"\t|  "+EK+"  "+EKgs+"  ;  "+"  +  "+Cexp+"  +  "+Eshift+"  ->  "+denom+"\t|\t"+tempval+"\t+=  "+M2nu+"\n")
peuq.close()
peq.close()
pKI.close()
pFK.close()

M2nu   = abs(M2nu)
qM2nu  = abs(qM2nu)
q1M2nu = abs(M2nu*0.82*0.82)
q2M2nu = abs(M2nu*0.77*0.77)
q3M2nu = abs(M2nu*0.74*0.74)

#output screen
print("... and the caclulations come to!\n\n")
print("M2nu           = "+M2nu+"\n")
print("M2nu*"+qf+"*"+qf+" = "+qM2nu+"\n")
print("M2nu*0.82*0.82 = "+q1M2nu+"\n")
print("M2nu*0.77*0.77 = "+q2M2nu+"\n")
print("M2nu*0.74*0.74 = "+q3M2nu+"\n")

#output to file
f.write("... and the caclulations come to!\n\n")
f.write("M2nu           = "+M2nu+"\n")
f.write("M2nu*"+qf+"*"+qf+" = "+qM2nu+"\n")
f.write("M2nu*0.82*0.82 = "+q1M2nu+"\n")
f.write("M2nu*0.77*0.77 = "+q2M2nu+"\n")
f.write("M2nu*0.74*0.74 = "+q3M2nu+"\n")

# output some reminders to screen
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')
print("check:  ./"+mydir+"/"+outdir+"/"+outfile+"\n")
print("run:    ./"+mydir+"/"+outdir+"/gnuplot "+plotsh1+"\n")
print("run:    ./"+mydir+"/"+outdir+"/gnuplot "+plotsh1+"\n")
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
