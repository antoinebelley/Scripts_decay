##  goM0nu.py
##  By: Antoine Belley, based on goM0nu.sh by Charlie Payne
##  Copyright (C): 2019
##  Description
##  this script will automatically run nushellx and/or nutbar for an M0nu NME calculation
##  it will pull the relevant 0vbb operator information from an IMSRG evolution that has already been run
##  in particular, we calculate the decay: (ZI,A) -> (ZF,A) + 2e, where ZI=Z and ZF=Z+2
##  it will do all three of: GT, F, and/or T, depending on the barcode inputs
##  using 'BARE' for the flow is a special case whereby the sp/int is set phenomenologically via nushellx
##  alternatively, to manually set sp/int use the -o option, as described below (see "# override option 1" and "# override option 2" below)
##  please add executions of nushelx and nutbar to your PATH and such via .bashrc
##  this script will use nuqsub.sh from $imasms, as set below

import os
import shutil
import glob
import re
from subprocess import call,PIPE
from time import time,sleep
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("ZI",     help = "Atomic (proton) number of the initial nucleus (I)", type=int)
parser.add_argument("A",      help = "Mass number of the decay", type=int)
parser.add_argument("flow",   help = "'BARE', 'MAGNUS', 'HYBRID', etc")
parser.add_argument("sp",     help = "The deisred space to use in nushellx, see: nushellx/sps/label.dat")
parser.add_argument("int",    help = "The desired interraction to use in nushellx, see: nushellx/sps/label.dat")
parser.add_argument("int3N",  help = "A label for which 3N interraction file was used")
parser.add_argument("emax",   help = "Maximum energy to limit valence space. Keep consistent with M0nu operator files")
parser.add_argument("hw",     help = "Frequency for the harmonic oscillator basis. Keep consistent with M0nu operator files")
parser.add_argument("nushon", help = "'s1', 's2', 's12' or 'off', where s stands for stage ")
parser.add_argument("GTbar",  help = "The five letter barcode for the GT operator, to not run it in nutbar use 'zzzzz'")
parser.add_argument("Fbar",   help = "The five letter barcode for the F operator, to not run it in nutbar use 'zzzzz'")
parser.add_argument("Tbar",   help = "The five letter barcode for the F operator, to not run it in nutbar use 'zzzzz'")
parser.add_argument("-o","--override", action='store_true', help="Override the automatic search for *.int and *.sp, giving the user the chance to manually choose them. If chosen, you will be ask later on if you want choice 1 or 2: '1' = use <sp>, <int>, <GTbar>, <Fbar>, <Tbar>(intended for hybrid calculation of: NuShellX wave functions + IMSRG-evolved operator) '2' = reset <sp> and <int> to anything from $imaout (intended for hybrid calculation of: IMSRG-evolved wave functions + BARE operator)")
parser.add_argument("-x","--extra",nargs='?', help = "Add an extra argument for labelling.")
args = parser.parse_args()


## STAGES
##  stage 0 = making directories, setting up files and symlinks
##  stage 1 = the first nushellx calculation, for the initial nucleus (I)
##  stage 2 = the second nushellx calculation, for the final nucleus (F), and submit the symlinks
##  stage 3 = the nutbar calculation(s) for the overall M0nu NME(s), and make the results copying script (the latter of which requires running GT, F and/or T) 


neigI=5       # number of eigenstates for nushellx to calculate for the initial nucelus (I)
maxJI=6       # maximum total angular momentum of the initial nucleus' state (I)
delJI=1       # step size for the total angular momentum calculations (I)
neigF=5       # ...similar to above... (F)
maxJF=6       # ...similar to above... (F)
delJF=1       # ...similar to above... (F)
snoozer=1	# set the sleep time between stages [s]
tagit='IMSRG'     # a tag for the symlinks below
imaout=os.getcwd()#'/global/home/belley/imsrg/work/output/'   # this must point to where the IMSRG output files live
imasms='/globlal/home/belley/SMscrits/'   # " " " " " " nuqsub.py and executes.py scripts live
imamyr='/global/home/belley/imsrg/work/results/'    # " " " " " " nutbar results may be copied to
ormanual='0'
or1='1'
or2='2'
s1on='s1'
s2on='s2'
s12on='s12'
soff='off'
Zbar='zzzzz'
Ztime='zzzzzzzzzz'
Zid=00000

que='oak'         # to see which queues have been set, execute: qmgr -c "p s"
wall=384        # in [1,512],  walltime limit for qsub [hr]
ppn=32          # in [1,32],   the number of CPUs to use for the qsub
vmem=251        # in [1,251],  memory limit for qsub [GB]
nth=32          # in [1,32],   number of threads to use


#Function to get a timestamp when given a M0nu barcode
def timeit(barcode):
	try:
		timestamp = str(glob.glob(imaout+'/M0nu_header_'+barcode+'*.txt')[0])
		timestamp = re.sub(imaout+'M0nu_header_', '',timestamp)
		timestamp = re.sub(".txt","",timestamp)
		return timestamp

	except IndexError: 
		print('ERROR 2135: cannot find a barcode!')
		print("GTbar  = "+args.GTbar)
		print("Fbar   = "+args.Fbar)
		print("Tbar   = "+args.Tbar)
		print('Exiting...')
		exit(1)


#Atomic number after the decay
ZF = args.ZI+2

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

if delJI == 0:
	delJI = 1  # seems to be a default that nushellx sets, even if maxJI=0

if delJF == 0:
	delJF = 1 # seems to be a default that nushellx sets, even if maxJI=0

quni="hw"+args.hw+"_e"+args.emax # this is just to make the qsub's name more unique


# pre-check
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("NME       =  M0nu")
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("override  =  "+str(args.override))
print("extra     =  "+str(args.extra))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("A         =  "+str(args.A))
print("nucI      =  "+nucI)
print("ZI        =  "+str(args.ZI))
print("neigI     =  "+str(neigI))
print("maxJI     =  "+str(maxJI))
print("delJI     =  "+str(delJI))
print("nucF      =  "+nucF)
print("ZF        =  "+str(ZF))
print("neigF     =  "+str(neigF))
print("maxJF     =  "+str(maxJF))
print("delJF     =  "+str(delJF))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("flow      =  "+args.flow)
print("sp        =  "+args.sp)
print("int       =  "+args.int)
print("int3N     =  "+args.int3N)
print("emax      =  "+args.emax)
print("hw        =  "+args.hw)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("nushon    =  "+args.nushon)
print("GTbar     =  "+args.GTbar)
print("Fbar      =  "+args.Fbar)
print("Tbar      =  "+args.Tbar)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("que       =  "+que)
print("wall      =  "+str(wall))
print("ppn       =  "+str(ppn))
print("vmem      =  "+str(vmem))
print("nth       =  "+str(nth))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
incheck = input("Is this input acceptable?(Y/N):")
print("")

if incheck == 'n' or incheck == 'N':
	print("Exiting ...")
	exit(1)

if args.nushon != s1on and args.nushon != s2on and args.nushon != s12on and args.nushon != soff:
	print('ERROR 1862: invalid choice for nushon')
	print("nushon = "+args.nushon)
	print("Exiting...")
	exit(1)

#----------------------------------- STAGE 0 -----------------------------------

# get the relevant time stamps
print("Grabbing the relevant time stamps...")
print("")

GTtime=Ztime
Ftime=Ztime
Ttime=Ztime

if args.GTbar != Zbar:
	GTbar= timeit(args.GTbar)

if args.Fbar != Zbar:
	Fbar = timeit(args.Fbar)

if args.Tbar != Zbar:
	Tbar = timeit(args.Tbar)

sleep(snoozer)


#make the relevant directories
print("Making the relevant directories...")
print("")

os.makedirs(nucI, exist_ok=True)
os.chdir(nucI)
basedir = os.getcwd()

mydir="M0nu_"+args.flow+"_"+args.sp+"_"+args.int+"_"+args.int3N+"_e"+args.emax+"_hw"+args.hw

if args.extra:
	mydir = mydir+"_"+args.extra
try:
	os.makedirs(mydir)
except:
	shutil.rmtree(mydir)
	os.makedirs(mydir)
os.chdir(mydir)

nudirI   = 'nushxI_data'           # this directory will hold the nushellx data for $nucI
nudirF   = 'nushxF_data'           # " " " " " " " " $nucF
linkdir  = 'nushx_symlinks'        # this directory just holds the symlinks script and output from its clutser run
GTdir    = 'GT_'+GTbar             # this directory will hold the GT nutbar results
Fdir     = 'F_'+Fbar               # " " " " " F " "
Tdir     = 'T_'+Tbar               # " " " " " T " "


os.makedirs(nudirI)
os.makedirs(nudirF)
os.makedirs(linkdir)

if GTbar != Zbar :
	os.makedirs(GTdir)

if Fbar != Zbar :
	os.makedirs(Fdir)

if Tbar != Zbar :
	os.makedirs(Tdir)

sleep(snoozer)


# copy over the relevant files from the IMSRG output directory for nushellx (*.int and *.sp) and nutbar (*.op)
print('copying over the relevant files...')
print("")

GTheader = "M0nu_header_"+GTbar+".txt" 
Fheader  = "M0nu_header_"+Fbar+".txt"
Theader  = "M0nu_header_"+Tbar+".txt"
intfile  = "*"+GTbar+".int"
spfile   = "*"+GTbar+".sp"
if GTbar == Zbar and Fbar != Zbar:
	intfile  = "*"+Fbar+".int"
	spfile   = "*"+Fbar+".sp"
if GTbar == Zbar and Tbar != Zbar:
	intfile  = "*"+Tbar+".int"
	spfile   = "*"+Tbar+".sp"

#Go fetch the .sp and .int files when override is chosen
if args.override:
	override = oron
	print('Manual OVERRIDE in effect...')
	print("")
	print("Would you like to choose space/interraction files from <1|2>:")
	print("1) nushellx with sp = $sp and int = $int [hint: does nushellx/sps/label.dat have these sp/int?]")
	print("or")
	print("2) "+imaout)
	ormanual = input()
	print()
	if ormanual == '1':
		print('running with...')
		print("sp    = "+args.sp)
		print("int   = "+args.int)
		print("GTbar = "+GTbar)    # this could be (un)evolved, depending on the barcodes
		print("Fbar  = "+Fbar)     # " " " ", " " " "
		print("Tbar  = "+Tbar)     # " " " ", " " " "
		print("")
	elif ormanual == '2':
		print("From:  "+imaout)
		spfile  = input('Enter the name of the desired *.sp file: ')
		intfile = input('Enter the name of the desired *.int file:')
		spfile_path  = imaout+spfile
		intfile_path = imaout+intfile
		try:
			spfile_path = str(glob.glob(spfile_path)[0])
		except IndexError:
			print('ERROR 0152: cannot find the given *.sp file')
			print("spfile = "+spfile)
			print('Exiting...')
			exit(1)
		try:
			intfile_path = str(glob.glob(intfile_path)[0])
		except IndexError:
			print('ERROR 6847: cannot find the given *.int file')
			print("intfile = "+intfile)
			print('Exiting...')
			exit(1)
	else:
		print('ERROR 5818: invalid choice for ormanual')
		print("ormanual = "+ormanual)
		print('Exiting...')
		exit(1)

#Verifies that the .sp and .int file exists and copy them in the directories for nushell, exit otherwise
intfile_path = imaout+"/"+intfile
spfile_path  = imaout+"/"+spfile
try :
	intfile_path = str(glob.glob(intfile_path)[0])
	spfile_path  = str(glob.glob(spfile_path)[0])
	os.system("cp "+intfile_path+" "+spfile_path+" "+nudirI)
	os.system("cp "+intfile_path+" "+spfile_path+" "+nudirF)
except IndexError:
	if args.nushon != soff and args.flow != 'BARE' and ormanual != or1:
		print('ERROR 5294: cannot find the needed files for nushellx!')
		print("spfile  = "+spfile)
		print("intfile = "+intfile)
		print('Exiting...')
		exit(1)


if GTbar != Zbar:
	os.chdir(GTdir)
	op1b_path   = imaout+"/*"+GTbar+"_1b.op"
	op2b_path   = imaout+"/*"+GTbar+"_2b.op"
	header_path = imaout+"/"+GTheader
	try :
		op1b_path = str(glob.glob(op1b_path)[0])
		op2b_path  = str(glob.glob(op2b_path)[0])
		header_path  = str(glob.glob(header_path)[0])
		os.system("cp "+op1b_path+" "+op2b_path+" .")
		os.system("cp "+header_path+" ..")
		os.chdir('..')
	except IndexError:
		if args.nushon != soff and args.flow != 'BARE' and ormanual != or1:
			print('ERROR 3983: cannot find the needed files!')
			print(GTdir+" is likely empty")
			print('Exiting...')
			exit(1)

if Fbar != Zbar:
	os.chdir(Fdir)
	op1b_path   = imaout+"/*"+Fbar+"_1b.op"
	op2b_path   = imaout+"/*"+Fbar+"_2b.op"
	header_path = imaout+"/"+Fheader
	try :
		op1b_path = str(glob.glob(op1b_path)[0])
		op2b_path  = str(glob.glob(op2b_path)[0])
		header_path  = str(glob.glob(header_path)[0])
		os.system("cp "+op1b_path+" "+op2b_path+" .")
		os.system("cp "+header_path+" ..")
		os.chdir('..')
	except IndexError:
		if args.nushon != soff and args.flow != 'BARE' and ormanual != or1:
			print('ERROR 9101: cannot find the needed files!')
			print(Fdir+" is likely empty")
			print('Exiting...')
			exit(1)

if Tbar != Zbar:
	os.chdir(Tdir)
	op1b_path   = imaout+"/*"+Tbar+"_1b.op"
	op2b_path   = imaout+"/*"+Tbar+"_2b.op"
	header_path = imaout+"/"+Theader
	try :
		op1b_path = str(glob.glob(op1b_path)[0])
		op2b_path  = str(glob.glob(op2b_path)[0])
		header_path  = str(glob.glob(header_path)[0])
		os.system("cp "+op1b_path+" "+op2b_path+" .")
		os.system("cp "+header_path+" ..")
		os.chdir('..')
	except IndexError:
		if args.nushon != soff and args.flow != 'BARE' and ormanual != or1:
			print('ERROR 2409: cannot find the needed files!')
			print(Tdir+" is likely empty")
			print('Exiting...')
			exit(1)

sleep(snoozer)


#prepping all the relevant symlinks
print("Prepping all the relevant symlinks...")
print()

onebop = args.flow+"_M0nu_1b.op" # the symlink name for the 1b op
twobop = args.flow+"_M0nu_2b.op" # " " " " " 2b "
linkpy =  linkdir+".py"           # a script which will make additional symlinks, to be run after nushellx is done
os.chdir(linkdir)
f = open(linkpy,"w")
f.write("import os\n\n")
f.write("os.chdir(\""+basedir+"/"+mydir+"/"+nudirI+"\")\n")           
f.write("for tempf in os.listdir(os.getcwd()):\n\t")
f.write("if tempf.endswith(('.xvc','.nba','.prj','.sps','.sp','.lpt')):\n\t\t")
if GTbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirI+"/'+tempf+' ../"+GTdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the $nudirI to the GTdir
if Fbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirI+"/'+tempf+' ../"+Fdir+"/'+tempf)\n\t\t")  # " " " " " " " " " " " " " " " Fdir
if Tbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirI+"/'+tempf+' ../"+Tdir+"/'+tempf)\n\t")  # " " " " " " " " " " " " " " " Tdir

f.write("os.chdir(\""+basedir+"/"+mydir+"/"+nudirF+"\")\n")           
f.write("for tempf in os.listdir(os.getcwd()):\n\t")
f.write("if tempf.endswith(('.xvc','.nba','.prj','.sps','.sp','.lpt')):\n\t\t")
if GTbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirF+"/'+tempf+' ../"+GTdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the nudirF to the GTdir
if Fbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirF+"/'+tempf+' ../"+Fdir+"/'+tempf)\n\t\t")  # " " " " " " " " " " " " " " " Fdir
if Tbar!=Zbar:
	f.write("os.system('ln -sf ../"+nudirF+"/'+tempf+' ../"+Tdir+"/'+tempf)\n\t")  # " " " " " " " " " " " " " " " Tdir
f.close()
os.system('chmod 755 '+linkpy)

os.chdir('..')
if args.nushon != soff and args.flow != 'BARE' and ormanual != or1:
	os.chdir(nudirI)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
	os.chdir(nudirF)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
if GTbar != Zbar:
	os.chdir(GTdir)
	os.system("ln -sf *"+GTbar+"_1b.op "+onebop)
	os.system("ln -sf *"+GTbar+"_2b.op "+twobop)
	os.chdir('..')
if Fbar != Zbar:
	os.chdir(Fdir)
	os.system("ln -sf *"+Fbar+"_1b.op "+onebop)
	os.system("ln -sf *"+Fbar+"_2b.op "+twobop)
	os.chdir('..')
if Tbar != Zbar:
	os.chdir(Tdir)
	os.system("ln -sf *"+Tbar+"_1b.op "+onebop)
	os.system("ln -sf *"+Tbar+"_2b.op "+twobop)
	os.chdir('..')

sleep(snoozer)



#----------------------------------- STAGE 1 -----------------------------------

# run nushellx for the initial nucleus, $nucI
s1id    = Zid
nucIans = nucI+'.ans'
nucIao  = nucIans+'.o'

if args.nushon == s1on or args.nushon == s12on:
	os.chdir(nudirI)
	f = open(nucIans,"w") #Wil overwrite file if they already exists
	f.write('--------------------------------------------------\n')
	f.write("lpe,   "+str(neigI)+"             ! option (lpe or lan), neig (zero=10)\n")
	if args.flow != 'BARE' and ormanual != or1:
		f.write(tagit+"                ! model space (*.sp) name (a8)\n")
	else:
		f.write(args.sp+"                ! model space (*.sp) name (a8)\n")
	f.write('n                    ! any restrictions (y/n)\n')
	if args.flow != 'BARE' and ormanual != or1:
		f.write(tagit+"                ! model space (*.int) name (a8)\n")
	else:
		f.write(args.int+"                ! model space (*.int) name (a8)\n")
	f.write(" "+str(args.ZI)+"                  ! number of protons\n")
	f.write(" "+str(args.A)+"                  ! number of nucleons\n")
	f.write(" 0.0, "+str(maxJI)+".0, "+str(delJI)+".0,      ! min J, max J, del J\n")
	f.write('  0                  ! parity (0 for +) (1 for -) (2 for both)\n')
	f.write('--------------------------------------------------\n')
	f.write('st                   ! option\n')
	f.close()
	print("Setting up "+ nucIans+" for nushellx...")
	os.system("shell "+ nucIans+" >> "+nucIao) # set up files for nushellx, and divert stdout to file
	os.chdir('..')
	sleep(snoozer)


#----------------------------------- STAGE 2 -----------------------------------


# run nushellx for the final nucleus, $nucF
s2id = Zid # stage 2 que id, as a backup...
nucFans = nucF+'.ans'
nucFao  = nucFans+'.o'

if args.nushon == s2on or args.nushon == s12on:
	os.chdir(nudirF)
	try:
		nucIans_path = str(glob.glob("../"+nudirI+"/"+nucIans)[0])
		os.system('cp '+nucIans_path+' '+nucFans)
	except IndexError:
		print("ERROR 6659: cannot find nucIans = "+nucIans+" for nucFans editing")
		print("Exeiting...")
		exit(1)
	with open(nucFans,'r') as file:
		line = file.readlines()
	with open(nucFans,'w') as file:
		for i in range(len(line)):
			if re.sub(str(neigI),str(neigF),line[i])!= line[i]:
				file.write(re.sub(str(neigI),str(neigF),line[i]))
			elif re.sub(str(args.ZI),str(ZF),line[i]) != line[i]:
				file.write(re.sub(str(args.ZI),str(ZF),line[i]))
			elif re.sub(" 0.0, "+str(maxJI)+".0, "+str(delJI)+".0"," 0.0, "+str(maxJF)+".0, "+str(delJF)+".0",line[i]):
				file.write(re.sub(" 0.0, "+str(maxJI)+".0, "+str(delJI)+".0"," 0.0, "+str(maxJF)+".0, "+str(delJF)+".0",line[i]))
			else:
				file.write(line[i])
	print("Setting up "+ nucFans+" for nushellx...")
	os.system("shell "+ nucFans+" >> "+nucFao) # set up files for nushellx, and divert stdout to file
	os.chdir('..')
	sleep(snoozer)

#----------------------------------- STAGE 3 -----------------------------------

#run nutbar to get final NME results
s3id     = Zid           #satge 3 que id, as a backup...
outfile  = "nutbar_tensor0_"+nucF+"0.dat" #this should contain the results :)
nutrun   = "nutbar_"+nucF+"0" 
nutrunin = nutrun+".input"
f = open(nutrunin,"w")
if args.flow != 'Bare' and ormanual != or1:
	f.write(tagit+"\n")
else:
	f.write(sp+"\n")
f.write(nucI+"0\n")
f.write(nucF+"0\n")
f.write(onebop+' '+twobop)
f.write('0.0\n')
f.write('1\n')
f.write('0.0\n')
f.write('1\n')
f.write('\n')
f.close()
if GTbar != Zbar:
	os.chdir(GTdir)
	os.system("rm -f "+outfile)
	os.system("cp ../"+nutrunin+' '+nutrunin)
	os.chdir('..')
if Fbar != Zbar:
	os.chdir(Fdir)
	os.system("rm -f "+outfile)
	os.system("cp ../"+nutrunin+' '+nutrunin)
	os.chdir('..')
if Tbar != Zbar:
	os.chdir(Tdir)
	os.system("rm -f "+outfile)
	os.system("cp ../"+nutrunin+' '+nutrunin)
	os.chdir('..')
os.remove(nutrunin)

#---------------------------------SENDING JOB QUEUE----------------------------------


#Sends the job to qsub, where the executable to be run are in execute.py
command = "python "+imasms+"/nuqsub.py,'python "+imasms+"/execute.py' "+nucI+" M0nu_"+quni+" "+que+" "+str(wall)+" "+str(ppn)+" "+str(vnem)+" "+str(nth)
os.system(command)


#-----------------Write script to copy result into desired directory-------------------
mycppy='mycopies.py' # a script to copy the results to $imamyr
outfileGT='nutbar_tensor0_'+nucF+'0_'+GTbar+'.dat'
outfileF='nutbar_tensor0_'+nucF+'0_'+Fbar+'.dat'
outfileT='nutbar_tensor0_'+nucF+'0_'+Tbar+'.dat'
totmyr = imamyr+"M0nu/"+nucI+"/"+mydir

f = open(mcppy, "w")
f.write("os.mkdirs("+imamyr+"+M0nu, exist_ok=True)\n")
f.write("os.mkdirs("+imamyr+"M0nu/"+nucI+", exist_ok=True)\n")
f.write("os.mkdirs("+totmyr+")\n")
f.write("os.mkdirs("+totmyr+"/"+GTdir+")\n")
f.write("os.mkdirs("+totmyr+"/"+Fdir+")\n")
f.write("os.mkdirs("+totmyr+"/"+Tdir+")\n")
f.write("os.system(cp "+GTdir+"/"+nucI+"*.lpt "+totmyr+"/"+GTdir+")\n")
f.write("os.system(cp "+GTdir+"/"+nucF+"*.lpt "+totmyr+"/"+GTdir+")\n")
f.write("os.system(cp "+GTdir+"/"+outfileGT+" "+totmyr+"/"+GTdir+")\n")
f.write("os.system(cp "+Fdir+"/"+nucI+"*.lpt "+totmyr+"/"+Fdir+")\n")
f.write("os.system(cp "+Fdir+"/"+nucF+"*.lpt "+totmyr+"/"+Fdir+")\n")
f.write("os.system(cp "+Fdir+"/"+outfileF+" "+totmyr+"/"+Fdir+")\n")
f.write("os.system(cp "+Tdir+"/"+nucI+"*.lpt "+totmyr+"/"+Tdir+")\n")
f.write("os.system(cp "+Tdir+"/"+nucF+"*.lpt "+totmyr+"/"+Tdir+")\n")
f.write("os.system(cp "+Tdir+"/"+outfileT+" "+totmyr+"/"+Tdir+")\n")
f.close()
os.system('chmod 755 '+mcppy)