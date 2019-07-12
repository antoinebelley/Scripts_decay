##  goDGT.py
##  By: Antoine Belley
##  Copyright (C): 2019
## DESCRIPTION
##  this script will automatically run nushellx and/or nutbar for an DGT calculation
##  it will pull the relevant DGT operator information from an IMSRG evolution that has already been run

import os
import sys
from time import sleep
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('ZI',     help = 'Atomic (proton) number of the initial nucleus (I)', type=int)
parser.add_argument('A',      help = 'Mass number of the decay', type=int)
parser.add_argument('flow',   help = '"BARE", "MAGNUS", "HYBRID", etc')
parser.add_argument('BB',     help = '"OS", "HF", "3N", "2N" - acts as a descriptor to help find the DGT operator')
parser.add_argument('sp',     help = 'The deisred space to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int',    help = 'The desired interraction to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int3N',  help = 'A label for which 3N interraction file was used')
parser.add_argument('emax',   help = 'Maximum energy to limit valence space. Keep consistent with M0nu operator files')
parser.add_argument('hw',     help = 'Frequency for the harmonic oscillator basis. Keep consistent with M0nu operator files')
parser.add_argument('-t', '--time', action = 'store', default = '06:00:00', help = 'Wall time for the submission on cedar')
args = parser.parse_args()
snoozer = 1

#Paths were to find the files from the IMSRG and fro the job submission. You should change this to match your directory
if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
  imasms = '/global/home/belley/Scripts_decay/'                           # ' ' ' ' ' ' nuqsub.py script lives
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
  imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # ' ' ' ' ' ' nuqsub.py script lives
else:
  print('This cluster is not known')
  print('Add the paths to execute_M2nu.py in this cluster')
  print('Exiting...')
  exit(1)   


sys.path.append(imasms)
from decay import *


#Create the instance of the decay
DGT = DGT(Z = args.ZI, A = args.A, flow =args.flow, sp = args.sp, inter = args.int, int3N = args.int3N, emax = args.emax, hw = args.hw,  BB = args.BB)
# pre-check
DGT.verify_param()
#----------------------------------- STAGE 0 -----------------------------------
#make the relevant directories
DGT.make_directories()
sleep(snoozer)
# copy over the relevant files from the IMSRG output directory for nushellx (*.int and *.sp) and nutbar (*.op)
DGT.copy_files()
sleep(snoozer)
#prepping all the relevant symlinks\write linkpy
DGT.prep_symlinks()
sleep(snoozer)
#----------------------------------- STAGE 1 -----------------------------------
# run nushellx 
DGT.write_nushell_files()
#----------------------------------- STAGE 2 -----------------------------------
#run nutbar to get final NME results
DGT.write_nutbar_files()
#---------------------------------SENDING JOB QUEUE----------------------------------
#Sends the job to qsub, where the executable to be run are in execute.py
DGT.send_queue(args.time)


