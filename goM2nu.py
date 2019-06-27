##  goM2nu.py
##  By: Antoine Belley, based on nuM2nu.sh by Charlie Payne
##  Copyright (C): 2018
## DESCRIPTION
##  this script will automatically run nushellx and/or nutbar for an M2nu calculation
##  it will pull the relevant Gamow-Teller operator information from an IMSRG evolution that has already been run
##  after it is complete, to get the final NME summation you can execute sumM2nu.py (following a successful run of this script)
##  in particular, we calculate the decay: (ZI,A) -> (ZK,A) + e + v [fictituous intermediate state] -> (ZF,A) + 2e + 2v, where ZI=Z, ZK=Z+1, and ZF=Z+2
##  with: initial (I) -> intermediate (K) -> final (F)
##  using 'BARE' for the flow is a special case whereby the sp/int is set phenomenologically via nushellx
##  alternatively, to manually set sp/int use the -o option, as described below (see '# override option 1' and '# override option 2' below)
##  NOTE: you must add in the intermediate nuclear ground state's (g.s.) J+ and summed excited states' (s.e.s.) J+ to 'the g.s./s.e.s. if-else ladder' below
##  please add executions of nushellx and nutbar to your PATH and such via .bashrc
##  this will use nuqsub.py from imasms, as set below

import os
import sys
from time import sleep
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('ZI',     help = 'Atomic (proton) number of the initial nucleus (I)', type=int)
parser.add_argument('A',      help = 'Mass number of the decay', type=int)
parser.add_argument('flow',   help = '"BARE", "MAGNUS", "HYBRID", etc')
parser.add_argument('BB',     help = '"OS", "HF", "3N", "2N" - acts as a descriptor to help find the GT operator in $imaout, see $filebase below')
parser.add_argument('sp',     help = 'The deisred space to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int',    help = 'The desired interraction to use in nushellx, see: nushellx/sps/label.dat')
parser.add_argument('int3N',  help = 'A label for which 3N interraction file was used')
parser.add_argument('emax',   help = 'Maximum energy to limit valence space. Keep consistent with M0nu operator files')
parser.add_argument('hw',     help = 'Frequency for the harmonic oscillator basis. Keep consistent with M0nu operator files')
parser.add_argument('neigK',  help = 'The number of eigenstates to create for summing over the K excitation energies', type=int)
parser.add_argument('-m','--mec', action='store_true', help ='Find a GT operator with meson exchange currents (MECs)')
parser.add_argument('-t', '--time', action = 'store', default = '24:00:00', help = 'Wall time for the submission on cedar')
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
if args.mec == True:
  M2nu = M2nu(Z = args.ZI, A = args.A, flow =args.flow, sp = args.sp, inter = args.int, int3N = args.int3N, emax = args.emax, hw = args.hw, neigK = args.neigK, BB = args.BB, MEC = True)
else:
  M2nu = M2nu(Z = args.ZI, A = args.A, flow = args.flow, sp = args.sp, inter = args.int, int3N = args.int3N, emax = args.emax, hw = args.hw, neigK = args.neigK, BB = args.BB)
# pre-check
M2nu.verify_param()
#----------------------------------- STAGE 0 -----------------------------------
#make the relevant directories
M2nu.make_directories()
sleep(snoozer)
# copy over the relevant files from the IMSRG output directory for nushellx (*.int and *.sp) and nutbar (*.op)
M2nu.copy_files()
sleep(snoozer)
#prepping all the relevant symlinks\write linkpy
M2nu.prep_symlinks()
sleep(snoozer)
#----------------------------------- STAGE 1 -----------------------------------
# run nushellx 
M2nu.write_nushell_files()
#----------------------------------- STAGE 2 -----------------------------------
#run nutbar to get final NME results
M2nu.write_nutbar_files()
#---------------------------------SENDING JOB QUEUE----------------------------------
#Sends the job to qsub, where the executable to be run are in execute.py
M2nu.send_queue(args.time)
#-----------------Write script to copy result into desired directory-------------------
# mycppy = 'mycopy.py'
# totmyr = imamyr+'M2nu/'+nucI+'/'+mydir

# f = open(mycppy, 'w')
# f.write('os.mkdirs('+imamyr+'+M2nu, exist_ok=True)\n')
# f.write('os.mkdirs('+imamyr+'M2nu/'+nucI+', exist_ok=True)\n')
# f.write('os.mkdirs('+totmyr+')\n')
# f.write('os.mkdirs('+totmyr+'/'+nudirI+')\n')
# f.write('os.mkdirs('+totmyr+'/'+nudirKgs+')\n')
# f.write('os.mkdirs('+totmyr+'/'+nudirK+')\n')
# f.write('os.mkdirs('+totmyr+'/'+nudirF+')\n')
# f.write('os.mkdirs('+totmyr+'/'+KIdir+')\n')
# f.write('os.mkdirs('+totmyr+'/'+FKdir+')\n')
# f.write('os.system(cp '+nudirI+'/'+nucI+'*.lpt '+totmyr+'/'+nudirI+')\n')
# f.write('os.system(cp '+nudirKgs+'/'+nucK+'*.lpt '+totmyr+'/'+nudirKgs+')\n')
# f.write('os.system(cp '+nudirK+'/'+nucK+'*.lpt '+totmyr+'/'+nudirK+')\n')
# f.write('os.system(cp '+nudirF+'/'+nucF+'*.lpt '+totmyr+'/'+nudirF+')\n')
# f.write('os.system(cp '+KIdir+'/'+outfile4+' '+totmyr+'/'+KIdir+')\n')
# f.write('os.system(cp '+FKdir+'/'+outfile5+' '+totmyr+'/'+FKdir+')\n')
# f.write('cp -R sumM2nu_* '+totmyr)  # NOTE: technically none of these will exist until sumM2nu.py is run
# f.close()
# st = os.stat(mycppy)
# os.chmod(mycppy ,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )

