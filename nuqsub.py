## This python script will create a PBS script and qsub it to the cluster
## the stdout of this script is the qsubbed job id
## it will put the output in the $PWD from which the script is called
## if argumement ${9} is not empty, then this qsubbed job will wait on H until the job in ${9} has finished
##  By: Antoine belley based on nuqsub.sh from Charlie Payne
##  Copyright (C): 2019


import os
import argparse
import shutil
from subprocess import call,PIPE
from time import time,sleep
from datetime import datetime
from sys import argv

parser = argparse.ArgumentParser()
parser.add_argument("mycmd",     help = "The terminal execution command, eg) for nushellx it is like '. ca48.bat' and for nutbar it is 'nutbar nutbar_ca480.input'")
parser.add_argument("myrun",     help = "The run name, eg) for nushellx it is the basename of *.ans and for nutbar it is the basename of *.input")
parser.add_argument("mybarcode", help = "An additional barcode to make the run name more unqiue in the qsub (if undesired then enter 'off'")
parser.add_argument("myque",     help = "To see which queues have been set, execute: qmgr -c 'p s'")
parser.add_argument("mywall",    help = "In [1,$mywallmax],  walltime limit for qsub [hr]", type = int)
parser.add_argument("myppn",     help = "In [1,$myppnmax],   the number of CPUs to use for the qsub", type = int)
parser.add_argument("myvmem",    help = "In [1,$myvmemmax],  memory limit for qsub [GB]", type = int)
parser.add_argument("mynth"      help = "In [1,$mynthmax],   number of threads to use", type = int)
parser.add_argument("-p","--pastid", action='store', default=00000, help ='A currently running qsub id, or leave it empty' )
args = parser.parse_args()

mycmd       = args.mycmd
myrun       = args.myrun
mybarcode   = args.mybarcode
myque       = args.myque
mywall      = args.mywall
myppn       = args.myppn
myvmem      = args.myvmem
mynth       = args.mynth
pastid      = args.pastid
myqtag      = 'login1'   #the cluster tag that appears in the job id
myqid       = 5          #the number of digits in the job id (this could change over time keep it updated!)




### Check to see what type of batch submission system we're dealing with
BATCHSYS = 'NONE'
if call('type '+'qsub', shell=True, stdout=PIPE, stderr=PIPE) == 0: BATCHSYS = 'PBS'
elif call('type '+'srun', shell=True, stdout=PIPE, stderr=PIPE) == 0: BATCHSYS = 'SLURM'

### Flag to swith between submitting to the scheduler or running in the current shell
#batch_mode=False
batch_mode=True
if 'terminal' in argv[1:]: batch_mode=False

#DON'T FORGET TO CHANGE THIS!!!! This email will receive job completetion alerts.
myemail = 'antoine.belley@mail.mcgill.ca' 

#pre-check
mywallmin = 1
mywallmax = 512
myppnmin   = 1
myppnmax  = 32 
myvmemmin = 1
myvmemmax = 251
mynthmin = 1
mynthmax  = 32
if mywall < mywallmin:
	mywall = mywallmin 
elif mywall > mywallmax:
	mywall = mywallmax
if myppn < myppnmin:
	myppn = myppnmin
elif myppn > myppnmax:
	myppn = myppnmax
if myvmem < myvmemmin:
	myvmem = myvmemmin
elif myvmem > myvmemmax:
	myvmem = myvmemmax
if mynthmax < mynthmin:
	mynth = mynthmin
elif mynth > mynthmax:
	mynth = mynthmax

### Make the cluster run files (PBS or SLURM)
if BATCHSYS == 'PBS':
  FILECONTENT = """#!/bin/bash
#PBS -N %s
#PBS -q oak
#PBS -d %s
#PBS -l walltime=512:00:00
#PBS -l nodes=1:ppn=%d
#PBS -l vmem=%sgb
#PBS -m ae
#PBS -M %s
#PBS -j oe
#PBS -o %s.pbs.o
cd $PBS_O_WORKDIR
export OMP_NUM_THREADS=%d
%s
"""

elif BATCHSYS == 'SLURM':
  FILECONTENT = """#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=%d
#SBATCH --output=imsrg_log/%s.%%j
#SBATCH --time=%s
#SBATCH --mail-user=%s
#SBATCH --mail-type=END
cd $SLURM_SUBMIT_DIR
echo NTHREADS = %d
export OMP_NUM_THREADS=%d
time srun %s
"""


logname=mybarcode+'_'+myrun

### Make an estimate of how much time to request. Only used for slurm at the moment.
time_request = '24:00:00'
#if   e <  5 : time_request = '00:10:00'
#elif e <  8 : time_request = '01:00:00'
#elif e < 10 : time_request = '04:00:00'
#elif e < 12 : time_request = '12:00:00'


### Submit the job if we're running in batch mode, otherwise just run in the current shell
if batch_mode==True:
   sfile = open(jobname+'.batch','w')
   if BATCHSYS == 'PBS':
     sfile.write(FILECONTENT%(myrun,environ['PWD'],myppn,myvmem,myemail,logname,mynth,mycmd))
     sfile.close()
     call(['qsub', jobname+'.batch'])
   elif BATCHSYS == 'SLURM':
     sfile.write(FILECONTENT%(mynth,myrun,time_request,myemail,mynth,mynth,mycmd))
     sfile.close()
     call(['sbatch', jobname+'.batch'])
   remove(jobname+'.batch') # delete the file
   sleep(0.1)
else:
   call(cmd.split())  # Run in the terminal, rather than submitting
