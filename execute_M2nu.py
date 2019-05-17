import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("srun",    help = "'s1', 's2', 's12' or 'off', where s stands for stage ")
parser.add_argument("nucI",    help = "Initial nucleus" )
parser.add_argument("nucK",    help = "Intermediate nucleus")
parser.add_argument("nucF",    help = "Initial nucleus" )
args = parser.parse_args()

runon='on'
srun    = list(args.srun)
s1run   = srun[0]
s2run   = srun[1]
s3run   = srun[2] 
s4run   = srun[3]
s5run   = srun[4]



#If you change any of these make sure that they match with the names in goM2nu.py
nudirI    = 'nushxI_data'      # this directory will hold the nushellx data for $nucI
nudirKgs  = 'gs_nushxK_data'   # " " " " " " " " the ground state of $nucK
nudirK    = 'nushxK_data'      # " " " " " " " " $nucK
nudirF    = 'nushxF_data'      # " " " " " " " " $nucF
linkdir   = 'nushx_symlinks'   # this directory just holds the symlinks script and output from its clutser run
KIdir     = 'KI_nutbar'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdir     = 'FK_nutbar'        #" " " " " < F | \sigma\tau | K > " "
nutrun4   = "nutbar_"+args.nucK+"0" 
nutrun4in = nutrun4+".input"
nutrun5   = "nutbar_"+args.nucF+"0" 
nutrun5in = nutrun5+".input"
PWD       = '/home/belleya/scratch/belleya/M2nu/ca48/M2nu_MAGNUS_3N_IMSRGfp_magic_magic_e10_hw16_neig250_MEC/'
linkpy =  linkdir+".py" 

cmd_s1       = "bash -c "+PWD+"/"+nudirI+"/"+args.nucI+".bat"
cmd_s2_gs    = "bash -c "+PWD+"/"+nudirKgs+"/"+args.nucK+".bat"
cmd_s2_ses   = "bash -c "+PWD+"/"+nudirK+"/"+args.nucK+".bat"
cmd_s3       = "bash -c "+PWD+"/"+nudirF+"/"+args.nucF+".bat"
cmd_links    = "python "+PWD+linkdir+"/"+linkpy
cmd_s4       = "nutbar "+PWD+"/"+KIdir+"/"+nutrun4in
cmd_s5       = "nutbar "+PWD+"/"+FKdir+"/"+nutrun5in

def execute_stage1():
	#Run nushell fot the initial state
	os.system(cmd_s1)

def execute_stage2():
	#Run nushell for the intermediate state (both gs and ses)
	os.system(cmd_s2_gs)
	os.system(cmd_s2_ses)

def execute_stage3():
	#Run nushell for the final stage
	os.system(cmd_s3)

def execute_links():
	#Run linkpy, dependant on how I run nushellx
	os.system(cmd_links)

def execute_stage4():
	#Run nutbar for Intermediate-Initial step
	os.system(cmd_s4)

def execute_stage5():
	#Run nutbar for Final-intermediate step
	os.system(cmd_s5)

if s1run == runon:
	execute_stage1()
if s2run == runon:
	execute_stage2()
if s3run == runon:
	execute_stage3()
execute_links()
if s4run == runon:
	execute_stage4()
if s5run == runon:
	execute_stage5()
