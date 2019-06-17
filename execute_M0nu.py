import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("nushon",  help = "'s1', 's2', 's12' or 'off', where s stands for stage ")
parser.add_argument("nucI",    help = "Initial nucleus" )
parser.add_argument("nucF",    help = "Initial nucleus" )
parser.add_argument("GTbar",   help = "Barcode for GT")
parser.add_argument("Fbar",    help = "Barcode for F")
parser.add_argument("Tbar",    help = "Barcode for T")
parser.add_argument("mydir",   help = "Directory for the whole run")
args = parser.parse_args()

s1on  ='s1'
s2on  ='s2'
s12on ='s12'
soff  ='off'


#If you change any of these make sure that they match with the names in goM0nu.py
nudirI   = 'nushxI_data'           # this directory will hold the nushellx data for $nucI
nudirF   = 'nushxF_data'           # " " " " " " " " $nucF
linkdir  = 'nushx_symlinks'        # this directory just holds the symlinks script and output from its clutser run
linkpy   =  linkdir+".py"
GTdir    = 'GT_'+args.GTbar             # this directory will hold the GT nutbar results
Fdir     = 'F_'+args.Fbar               # " " " " " F " "
Tdir     = 'T_'+args.Tbar               # " " " " " T " "
nutrun   = "nutbar_"+args.nucF+"0" 
nutrunin = nutrun+".input"
Zbar     = 'zzzzz'
PWD = '/home/belleya/scratch/belleya/M0nu/'
if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
	PWD = "/global/scratch/belley/M0vu/"
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
	PWD = '/home/belleya/scratch/belleya/M0nu/'


bat_s1       = "./"+args.nucI+".bat"
bat_s2       = "./"+args.nucF+".bat"
linkpy       = "./"+linkdir+".py" 

def command(file):
	if file.endswith(".py"):
		cmd = "python "+file
	elif file.endswith(".input"):
		cmd = "nutbar "+file
	elif file.endswith(".bat"):
		cmd = "bash -c "+file
	else:
		print("File doesn't have the right extension.")
		print("Exiting...")
		exit(1)
	return cmd 


def execute_stage1(): 
	#Run nushell fot the initial state
	os.chdir(nudirI)
	os.system(command(bat_s1))
	os.chdir('..')
	
def execute_stage2():
	#Run nushelll for the final state
	os.chdir(nudirF)
	os.system(command(bat_s2))
	os.chdir('..')

def execute_links():
	#Run linkpy, dependant on how I've run nushellx	
	os.chdir(linkdir)
	os.system(command(linkpy))
	os.chdir('..')

def execute_stage3():
	#Run nutbar for Gammow teller transition if files given
	if args.GTbar != Zbar:
		os.chdir(GTdir)
		os.system(command(nutrunin))
		os.chdir('..')
	if args.Fbar != Zbar:
		os.chdir(Fdir)
		os.system(command(nutrunin))
		os.chdir('..')
	if args.Tbar != Zbar:
		os.chdir(Tdir)
		os.system(command(nutrunin))
		os.chdir('..')

os.chdir(PWD+args.nucI+"/"+args.mydir+"/")
if args.nushon == soff:
	execute_stage3()#Run nutbar
if args.nushon == s1on:
	execute_stage1()#Run nushelll for initial state
	execute_links() #Create symplinks
	execute_stage3()#Run nutbar
if args.nushon == s2on:
	execute_stage2()#Run nushelll for final state
	execute_links() #Create symlinks
	execute_stage3()#Run nutbar
if args.nushon == s12on:
	execute_stage1()#Run nushelll for initial state
	execute_stage2()#Run nushelll for final state
	execute_links() #Create symlinks
	execute_stage3()#Run nutbar
os.system('rm -f execute_M0nu.sh')
		