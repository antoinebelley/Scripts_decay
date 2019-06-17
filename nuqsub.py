## This python script will create a PBS script and qsub it to the cluster
## the stdout of this script is the qsubbed job id
## it will put the output in the $PWD from which the script is called
## if argumement ${9} is not empty, then this qsubbed job will wait on H until the job in ${9} has finished
##  By: Antoine belley based on nuqsub.sh from Charlie Payne and goUniversal.py from Ragnar Stroberg
##  Copyright (C): 2019

import os
import argparse
from subprocess import call,PIPE
from time import sleep
from sys import argv
from cluster_class import oak, cedar

parser = argparse.ArgumentParser()
parser.add_argument("mycmd",     help = "The terminal execution command, eg) for nushellx it is like '. ca48.bat' and for nutbar it is 'nutbar nutbar_ca480.input'")
parser.add_argument("myrun",     help = "The run name, eg) for nushellx it is the basename of *.ans and for nutbar it is the basename of *.input")
parser.add_argument("mybarcode", help = "An additional barcode to make the run name more unqiue in the qsub (if undesired then enter 'off'")
parser.add_argument("-w", "--mywall", nargs=1, action='store',   help = "In [1,$mywallmax],  walltime limit for qsub [hr]", type = int)
parser.add_argument("-p", "--myppn", nargs=1, action='store',    help = "In [1,$myppnmax],   the number of CPUs to use for the qsub", type = int)
parser.add_argument("-m", "--myvmem", nargs=1, action='store',   help = "In [1,$myvmemmax],  memory limit for qsub [GB]", type = int)
parser.add_argument("-n", "--mynth" ,  nargs=1, action='store',  help = "In [1,$mynthmax],   number of threads to use", type = int)
parser.add_argument("-t", "--time", nargs=1, action='store' ,default='24:00:00', help = "Time request if you use cedar. Default is 24:00:00")
args = parser.parse_args()

mycmd        = args.mycmd
myrun        = args.myrun
mybarcode    = args.mybarcode
mywall       = args.mywall
myppn        = args.myppn
myvmem       = args.myvmem
mynth        = args.mynth
time_request = args.time[0]


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
myrun=mybarcode+'_'+myrun


### Submit the job if we're running in batch mode, otherwise just run in the current shell
if batch_mode==True:
    if BATCHSYS == 'PBS':
        if str(os.environ['HOSTNAME']) == oak.host:
            oak.submit_job(mycmd,myrun,myemail)
        else:
            print('Cluster is not known. Please create an instance for it.')
            print('Exiting...')
            exit(1)
    elif BATCHSYS == 'SLURM':
        if str(os.environ['HOSTNAME'])[7:] == cedar.host: 
            cedar.submit_job(mycmd,myrun, myemail, time = time_request)
        else:
            print('Cluster is not known. Please create an instance for it.')
            print('Exiting...')
            exit(1)
    sleep(0.1)
else:
    call(mycmd.split())  # Run in the terminal, rather than submitting