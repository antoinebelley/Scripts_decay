import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("nushon",  help = "'s1', 's2', 's12' or 'off', where s stands for stage ")
parser.add_argument("nucI",    help = "Initial nucleus" )
parser.add_argument("nucF",    help = "Initial nucleus" )
parser.add_argument("quni",    help = "Makes the qsub more unique: should be of the form hw##_emax##")
parser.add_argument("GTbar",   help = "Barcode for GT")
parser.add_argument("Fbar",    help = "Barcode for F")
parser.add_argument("Tbar",    help = "Barcode for T")
parser.add_argument("mydir",   help = "Directory for the whole run")
args = parser.parse_args()

s1on  ='s1'
s2on  ='s2'
s12on ='s12'
soff  ='off'
Zid   = 00000
Zbar  ='zzzzz'

os.chdir(args.nucI+"/"+args.mydir)

#If you change any of these make sure that they match with the names in goM0nu.py
nudirI   = 'nushxI_data'           # this directory will hold the nushellx data for $nucI
nudirF   = 'nushxF_data'           # " " " " " " " " $nucF
linkdir  = 'nushx_symlinks'        # this directory just holds the symlinks script and output from its clutser run
linkpy   =  linkdir+".py"
GTdir    = 'GT_'+args.GTbar             # this directory will hold the GT nutbar results
Fdir     = 'F_'+args.Fbar               # " " " " " F " "
Tdir     = 'T_'+args.Tbar               # " " " " " T " "
outfile  = "nutbar_tensor0_"+args.nucF+"0.dat" #this should contain the results :)
nutrun   = "nutbar_"+args.nucF+"0" 
nutrunin = nutrun+".input"
PWD      = os.getcwd()         

cmd_s1       = "bash -c ."+PWD+"/"+nudirI+"/"+args.nucI+".bat"
cmd_s2       = "bash -c ."+PWD+"/"+nudirF+"/"+args.nucF+".bat"
cmd_s2_links = "python ."+PWD+"/"+linkdir+"/"+linkpy
cmd_s3_GT    = "nutbar "+PWD+"/"+GTdir+"/"+nutrunin
cmd_s3_F     = "nutbar "+PWD+"/"+Fdir+"/"+nutrunin
cmd_s3_T     = "nutbar "+PWD+"/"+Tdir+"/"+nutrunin


def execute_stage1(): 
	#Run nushelll for initial state  
	os.system(cmd_s1)
	
def execute_stage2():
	#Run nushelll for final state
	os.system(cmd_s2)
	#Run linkpy, dependant on how I've run nushellx
	os.system(cmd_s2_links)

def execute_stage3():
	#Run nutbar for Gammow teller transition if files given
	if args.GTbar != Zbar:
		os.system(cmd_s3_GT)
	if args.Fbar != Zbar:
		os.system(cmd_s3_F)
	if args.Tbar != Zbar:
		os.system(cmd_s3_T)

if args.nushon == soff:
	execute_stage3()#Run nutbar
if args.nushon == s1on:
	execute_stage1()#Run nushelll for initial state
	execute_stage3()#Run nutbar
if args.nushon == s2on:
	execute_stage2()#Run nushelll for final state
	execute_stage3()#Run nutbar
if args.nushon == s12on:
	execute_stage1()#Run nushelll for initial state
	execute_stage2()#Run nushelll for final state
	execute_stage3()#Run nutbar
		