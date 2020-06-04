##  goM0nu.py
##  By: Antoine Belley, based on goM0nu.sh by Charlie Payne
##  Copyright (C): 2019
##  Description
##  this script will automatically run nushellx and/or nutbar for an M0nu NME calculation
##  it will pull the relevant 0vbb operator information from an IMSRG evolution that has already been run
##  in particular, we calculate the decay: (ZI,A) -> (ZF,A) + 2e, where ZI=Z and ZF=Z+2
##  it will do all three of: GT, F, and/or T, depending on the barcode inputs
##  using 'BARE' for the flow is a special case whereby the sp/int is set phenomenologically via nushellx
##  alternatively, to manually set sp/int use the -o option, as described below (see '# override option 1' and '# override option 2' below)
##  please add executions of nushelx and nutbar to your PATH and such via .bashrc
##  this script will use nuqsub.sh from $imasms, as set below
import os
import sys
import argparse
from time import sleep
parser = argparse.ArgumentParser()
parser.add_argument('ZI',     help = 'Atomic (proton) number of the initial nucleus (I)', type=int)
parser.add_argument('A',      help = 'Mass number of the decay', type=int)
parser.add_argument('flow',   help = '"BARE", "MAGNUS", "HYBRID", etc')
parser.add_argument('sp',     help = 'The deisred space to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int',    help = 'The desired interraction to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int3N',  help = 'A label for which 3N interraction file was used')
parser.add_argument('emax',   help = 'Maximum energy to limit valence space. Keep consistent with M0nu operator files')
parser.add_argument('hw',     help = 'Frequency for the harmonic oscillator basis. Keep consistent with M0nu operator files')
parser.add_argument('GTbar',  help = 'The five letter barcode for the GT operator')
parser.add_argument('Fbar',   help = 'The five letter barcode for the F operator')
parser.add_argument('Tbar',   help = 'The five letter barcode for the F operator')
parser.add_argument('-t', '--time', action = 'store', default = '00:30:00', help = 'Wall time for the submission on cedar')
args = parser.parse_args()
snoozer = 1
#Paths were to find the files from the IMSRG and fro the job submission. You should change this to match your directory
if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
    imasms = '/global/home/belley/Scripts_decay/'                           # ' ' ' ' ' ' nuqsub.py script lives
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
    imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # ' ' ' ' ' ' nuqsub.py script lives
else:
    print('This cluster is not known')
    print('Add the paths to execute_M0nu.py in this cluster')
    print('Exiting...')
    exit(1) 
sys.path.append(imasms)
from kshell_m0nu import *
#Create an instance of the decay
M0nu = M0nu(args.ZI, args.A, args.flow, args.sp, args.int, args.int3N, args.emax, args.hw, args.GTbar, args.Fbar, args.Tbar)
# pre-check
M0nu.verify_param()
#----------------------------------- STAGE 0 ------------------------------------
#make the relevant directories
M0nu.make_directories()
sleep(snoozer)
# copy over the relevant files from the IMSRG output directory for nushellx (*.int and *.sp) and nutbar (*.op)
M0nu.copy_files()
sleep(snoozer)
#prepping all the relevant symlinks\write linkpy
M0nu.prep_symlinks()
sleep(snoozer)

#---------------------------------SENDING JOB QUEUE----------------------------------
#Sends the job to qsub, where the executable to be run are in execute.py
M0nu.send_queue(args.time)

