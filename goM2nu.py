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
##  alternatively, to manually set sp/int use the -o option, as described below (see "# override option 1" and "# override option 2" below)
##  NOTE: you must add in the intermediate nuclear ground state's (g.s.) J+ and summed excited states' (s.e.s.) J+ to "the g.s./s.e.s. if-else ladder" below
##  please add executions of nushellx and nutbar to your PATH and such via .bashrc
##  this will use nuqsub.py from imasms, as set below

import os
import shutil
import glob
import re
from time import sleep
import argparse
from write_evolve_file import *

parser = argparse.ArgumentParser()
parser.add_argument("ZI",     help = "Atomic (proton) number of the initial nucleus (I)", type=int)
parser.add_argument("A",      help = "Mass number of the decay", type=int)
parser.add_argument("flow",   help = "'BARE', 'MAGNUS', 'HYBRID', etc")
parser.add_argument("BB",     help = "'OS', 'HF', '3N', '2N' - acts as a descriptor to help find the GT operator in $imaout, see $filebase below")
parser.add_argument("sp",     help = "The deisred space to use in nushellx, see: nushellx/sps/label.dat")
parser.add_argument("int",    help = "The desired interraction to use in nushellx, see: nushellx/sps/label.dat")
parser.add_argument("int3N",  help = "A label for which 3N interraction file was used")
parser.add_argument("emax",   help = "Maximum energy to limit valence space. Keep consistent with M0nu operator files")
parser.add_argument("hw",     help = "Frequency for the harmonic oscillator basis. Keep consistent with M0nu operator files")
parser.add_argument("srun",   help = "For eg) Q0QQQ = run stage 1, skip stage 2, and run stages 3-5")
parser.add_argument("neigK",  help = "The number of eigenstates to create for summing over the K excitation energies", type=int)
parser.add_argument("-o","--override", action='store_true', help="Override the automatic search for *.int and *.sp, giving the user the chance to manually choose them. If chosen, you will be ask later on if you want choice 1 or 2: '1' = use <sp>, <int>, <GTbar>, <Fbar>, <Tbar>(intended for hybrid calculation of: NuShellX wave functions + IMSRG-evolved operator) '2' = reset <sp> and <int> to anything from $imaout (intended for hybrid calculation of: IMSRG-evolved wave functions + BARE operator)")
parser.add_argument("-x","--extra",nargs='?', help = "Add an extra argument for labelling.")
parser.add_argument("-m","--mec", action='store_true', help ="Find a GT operator with meson exchange currents (MECs)")
args = parser.parse_args()

## STAGES
##  stage 0 = making directories, setting up files and symlinks
##  stage 1 = the first nushellx calculation, for the initial nucleus (I)
##  stage 2 = the second nushellx calculations, for the intermediate nucleus (K)
##  stage 3 = the third nushellx calculation, for the final nucleus (F), and submit the symlinks
##  stage 4 = the nutbar calculation for the initial nucleus to the intermediate nucleus
##  stage 5 = the nutbar calculation for the intermediate nucleus to the final nucleus, and make the results copying script (the latter of which doesn't require any queing)

neigI=5              # number of eigenstates for nushellx to calculate for the initial nucelus (I)
maxJI=6              # maximum total angular momentum of the initial nucleus' state (I)
delJI=1              # step size for the total angular momentum calculations (I)
maxJK=6              # ...similar to above... (K)
delJK=1              # ...similar to above... (K)
neigF=5              # ...similar to above... (F)
maxJF=6              # ...similar to above... (F)
delJF=1              # ...similar to above... (F)
snoozer=1              # set the sleep time between stages [s]
tagit='IMSRG'            # a tag for the symlinks below
catch='forM2nu'          # acts as a descriptor to help find the GT operator in $imaout, see $filebase below
catchGT='GamowTeller'    # " " " " " " " " " " " ", " " " (without MECs)
catchMEC='GTMEC'        # " " " " " " " " " " " ", " " " (with MECs)
imaout=os.getcwd()          # this must point to where the IMSRG output files live
imasms='/global/home/belley/Scripts_decay/'# " " " " " " nuqsub.sh script lives
imamyr='/global/home/belley/imsrg/work/results/'           # " " " " " " final results may be copied to
mecon='MEC'
ormanual='0'
oron='on'
or1='1'
or2='2'
runon='Q'
runoff='0'
Zid=000000


#Change the name of the file (see below) depending of if mec is chosen or not
if args.mec:
	mecopt = mecon
else:
	mecopt = 'off'


#Value for each stages and reference for future conditional statement
srun    = list(args.srun)
s1run   = srun[0]
s2run   = srun[1]
s3run   = srun[2] 
s4run   = srun[3]
s5run   = srun[4]
s123run = s1run+s2run+s3run 
s123off = runoff+runoff+runoff
salloff = runoff+runoff+runoff+runoff+runoff


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

if nucK == 'sc48':
	gsJK=6
	gsPK=0
	sesJK=1
	sesPK=0
else:
	print('ERROR 0429: the intermediate g.s./s.e.s. for this decay has not been set, please add them to the g.s./s.e.s. if-else ladder!') 
	print("nucK = "+nucK)
	print('Exiting...')
	exit(1)

if delJI == 0:
	delJI = 1  # seems to be a default that nushellx sets, even if maxJI=0

if delJK == 0:
	delJK = 1  # seems to be a default that nushellx sets, even if maxJI=0

if delJF == 0:
	delJF = 1 # seems to be a default that nushellx sets, even if maxJI=0

quni = mecopt+"_hw"+args.hw+"_e"+args.emax


# pre-check
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("NME       =  M2nu")
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("mecopt  =  "+str(mecopt))
print("override  =  "+str(args.override))
print("extra     =  "+str(args.extra))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("A         =  "+str(args.A))
print("nucI      =  "+nucI)
print("ZI        =  "+str(args.ZI))
print("neigI     =  "+str(neigI))
print("maxJI     =  "+str(maxJI))
print("delJI     =  "+str(delJI))
print("nucK      =  "+nucK)
print("ZK        =  "+str(ZK))
print("neigI     =  "+str(args.neigK))
print("maxJI     =  "+str(maxJK))
print("delJI     =  "+str(delJK))
print("nucF      =  "+nucF)
print("ZF        =  "+str(ZF))
print("neigF     =  "+str(neigF))
print("maxJF     =  "+str(maxJF))
print("delJF     =  "+str(delJF))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("flow      =  "+args.flow)
print("BB        =  "+args.BB)
print("sp        =  "+args.sp)
print("int       =  "+args.int)
print("int3N     =  "+args.int3N)
print("emax      =  "+args.emax)
print("hw        =  "+args.hw)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print("srun      =  "+s1run+s2run+s3run+s4run+s5run)
print("gsJK      =  "+str(gsJK))
print("gsPK      =  "+str(gsPK))
print("sesJK     =  "+str(sesJK))
print("sesPK     =  "+str(sesPK))
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
incheck = input("Is this input acceptable?(Y/N):")
print("")

if incheck == 'n' or incheck == 'N':
	print("Exiting ...")
	exit(1)

#Check that the choices for the runs are valid:
if s1run != runon and s1run != runoff:
	print('ERROR 9004: invalid choice for srun')
	print("s1run = "+s1run)
	print('Exiting...')
	exit(1)
if s2run != runon and s2run != runoff:
	print('ERROR 8717: invalid choice for srun')
	print("s2run = "+s2run)
	print('Exiting...')
	exit(1)
if s3run != runon and s3run != runoff:
	print('ERROR 3721: invalid choice for srun')
	print("s3run = "+s3run)
	print('Exiting...')
	exit(1)
if s4run != runon and s4run != runoff:
	print('ERROR 8265: invalid choice for srun')
	print("s4run = "+s4run)
	print('Exiting...')
	exit(1)
if s5run != runon and s5run != runoff:
	print('ERROR 1483: invalid choice for srun')
	print("s5run = "+s5run)
	print('Exiting...')
	exit(1)
#----------------------------------- STAGE 0 -----------------------------------

# find the relevant files
print("Finding the relevant files...\n")
temppwd = os.getcwd()
filebase="*"
if args.flow == 'BARE':
	filebase = filebase+args.flow+"*"+args.BB+"*"
elif args.int == 'magic':
	filebase = filebase+args.int+"*"+args.BB+"*"
else:
	filebase = filebase+args.BB+"*"+args.int+"*"
filebase = filebase+"e"+args.emax+"*hw"+args.hw+"*A"+str(args.A)+"*"+catch
intfile  = filebase+"_.int"
spfile   = filebase+"_.sp"
if mecopt == mecon:
	GT1bfile=filebase+"MEC_"+catchMEC+"_1b.op"
	GT2bfile=filebase+"MEC_"+catchMEC+"_2b.op"
else:
	GT1bfile=filebase+"_"+catchGT+"_1b.op"
	GT2bfile=filebase+"_"+catchGT+"_2b.op"

#Go fetch the .sp and .int files when override is chosen
if args.override:
	override = oron
	print('Manual OVERRIDE in effect...\n')
	print("Enter the name of the desired *_1b.op file:\n")
	print("(Make sure this file matches with the script parameters)\n")
	if args.mecopt:
		print('(Make sure this file has full MECs)\n')
	GT1bfile = input("")
	print("Enter the name of the desired *_2b.op file:\n")
	print("(Make sure this file matches with the script parameters)\n")
	if args.mecopt:
		print('(Make sure this file has full MECs)\n')
	GT2bfile = input("")
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

#Verifies that the .sp,.int and .op file exists and copy them in the directories for nushell, exit otherwise
intfile_path  = imaout+"/"+intfile
spfile_path   = imaout+"/"+spfile
GT1bfile_path = imaout+"/"+GT1bfile
GT2bfile_path = imaout+"/"+GT2bfile
try :
	intfile_path = str(glob.glob(intfile_path)[0])
except IndexError:
	if args.flow != 'BARE' and ormanual != or1:
		if args.override == oron:
			print('ERROR 7395: cannot find the given *.int file')
		else:
			print('ERROR 4991: cannot find the relevant *.int file')
		print("intfile = "+intfile)
		print('Exiting...')
		exit(1)
try :
	spfile_path = str(glob.glob(spfile_path)[0])
except IndexError:
	if args.flow != 'BARE' and ormanual != or1:
		if args.override == oron:
			print('ERROR 1828: cannot find the given *.sp file')
		else:
			print('ERROR 7059: cannot find the relevant *.sp file')
		print("spfile = "+spfile)
		print('Exiting...')
		exit(1)
try :
	GT1bfile_path = str(glob.glob(GT1bfile_path)[0])
except IndexError:
	if args.flow != 'BARE' and ormanual != or1:
		if args.override == oron:
			print('ERROR 7763: cannot find the given *_1b.op file')
		else:
			print('ERROR 5365: cannot find the relevant *_1b.op file')
		print("GT1bfile = "+GT1bfile)
		print('Exiting...')
		exit(1)
try :
	GT2bfile_path = str(glob.glob(GT2bfile_path)[0])
except IndexError:
	if args.flow != 'BARE' and ormanual != or1:
		if args.override == oron:
			print('ERROR 8476: cannot find the given *_2b.op file')
		else:
			print('ERROR 4552: cannot find the relevant *_2b.op file')
		print("GT2bfile = "+GT2bfile)
		print('Exiting...')
		exit(1)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
os.chdir(imaout)
if s123run != s123off and args.flow != 'BARE' and ormanual != or1:
	intlist = glob.glob(intfile_path)
	splist  = glob.glob(spfile_path)
	print("The *.int file is:\n")
	for file in intlist:
		print("\t"+file+"\n")
	print("The *.sp file is:\n")
	for file in splist:
		print("\t"+file+"\n")
GT1bfile_list = glob.glob(GT1bfile_path)
print("The *1b.op file is:")
for file in GT1bfile_list:
	print("\t"+file+"\n")
GT2bfile_list = glob.glob(GT2bfile_path)
print("The *2b.op file is:")
for file in GT2bfile_list:
	print("\t"+file+"\n")
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('NOTE: if multiple files are listed per *.int, *.sp, *1b.op, or *2b.op => you got problems!')
os.chdir(temppwd)
if args.override != oron:
	print("filebase ="+filebase)
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
incheck = input("Are these files acceptable?(Y/N):")
if incheck == 'n' or incheck == 'N':
	print("Exiting ...")
	exit(1)
sleep(snoozer)



#Make the relevant directories 
print('Making the relevant directories...\n')
os.makedirs(nucI, exist_ok=True)
os.chdir(nucI)

basedir = os.getcwd()
mydir="M2nu_"+args.flow+"_"+args.BB+"_"+args.sp+"_"+args.int+"_"+args.int3N+"_e"+args.emax+"_hw"+args.hw+"_neig"+str(args.neigK)

if args.mec:
	mydir = mydir+"_"+mecon
if args.extra:
	mydir = mydir+"_"+args.extra

try:
	os.makedirs(mydir)
except:
	shutil.rmtree(mydir)
	os.makedirs(mydir)
os.chdir(mydir)

nudirI   = 'nushxI_data'      # this directory will hold the nushellx data for $nucI
nudirKgs = 'gs_nushxK_data'   # " " " " " " " " the ground state of $nucK
nudirK   = 'nushxK_data'      # " " " " " " " " $nucK
nudirF   = 'nushxF_data'      # " " " " " " " " $nucF
linkdir  = 'nushx_symlinks'   # this directory just holds the symlinks script and output from its clutser run
KIdir    = 'KI_nutbar'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdir    = 'FK_nutbar'        #" " " " " < F | \sigma\tau | K > " "

os.makedirs(nudirI)
os.makedirs(nudirKgs)
os.makedirs(nudirK)
os.makedirs(nudirF)

os.makedirs(linkdir)
if s4run == runon:
	os.makedirs(KIdir)
if s5run == runon:
	os.makedirs(FKdir)

sleep(snoozer)


# copy over the relevant files from the IMSRG output directory for nushellx (*.int and *.sp) and nutbar (*.op)
print('Copying the relevant files...\n')
if s123run != s123off:
	try:
		intfile_path = str(glob.glob(intfile_path)[0])
		spfile_path  = str(glob.glob(spfile_path)[0])
		os.system("cp "+intfile_path+" "+spfile_path+" "+nudirI)
		os.system("cp "+intfile_path+" "+spfile_path+" "+nudirK)
		os.system("cp "+intfile_path+" "+spfile_path+" "+nudirKgs)
		os.system("cp "+intfile_path+" "+spfile_path+" "+nudirF)
	except IndexError:
		if args.flow != 'BARE' and ormanual != or1:
			print('ERROR 0610: cannot find the needed files for nushellx!')
			print("spfile  = "+spfile)
			print("intfile = "+intfile)
			print('Exiting...')
			exit(1)
if s4run == runon:
	try:
		GT1bfile_path = str(glob.glob(GT1bfile_path)[0])
		GT2bfile_path = str(glob.glob(GT2bfile_path)[0])
		os.system("cp "+GT1bfile_path+" "+GT2bfile_path+" "+KIdir)
	except IndexError:
		print('Cannot find the op files!')
		print('1b.op = '+GT1bfile)
		print('2b.op = '+GT2bfile)
if s5run == runon:
	try:
		GT1bfile_path = str(glob.glob(GT1bfile_path)[0])
		GT2bfile_path = str(glob.glob(GT2bfile_path)[0])
		os.system("cp "+GT1bfile_path+" "+GT2bfile_path+" "+FKdir)
	except IndexError:
		print('Cannot find the op files!')
		print('1b.op = '+GT1bfile)
		print('2b.op = '+GT2bfile)
sleep(snoozer)


##prepping all the relevant symlinks
print("Prepping all the relevant symlinks...\n")

onebop = args.flow+"_M2nu_1b.op" # the symlink name for the 1b op
twobop = args.flow+"_M2nu_2b.op" # " " " " " 2b "
linkpy =  linkdir+".py"           # a script which will make additional symlinks, to be run after nushellx is done

os.chdir(linkdir)

f = open(linkpy,"w")
f.write("import os\n\n")
f.write("os.chdir(\""+basedir+"/"+mydir+"/"+nudirI+"\")\n")           
f.write("for tempf in os.listdir(os.getcwd()):\n\t")
f.write("if tempf.endswith(('.xvc','.nba','.prj','.sps','.sp','.lpt')):\n\t\t")
if s4run == runon:
	f.write("os.system('ln -sf ../"+nudirI+"/'+tempf+' ../"+KIdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the $nudirI to the KIdir
f.write("os.chdir(\""+basedir+"/"+mydir+"/"+nudirK+"\")\n")           
f.write("for tempf in os.listdir(os.getcwd()):\n\t")
f.write("if tempf.endswith(('.xvc','.nba','.prj','.sps','.sp','.lpt')):\n\t\t")
if s4run == runon:
	f.write("os.system('ln -sf ../"+nudirK+"/'+tempf+' ../"+KIdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the $nudirK to the KIdir
if s5run == runon:
	f.write("os.system('ln -sf ../"+nudirK+"/'+tempf+' ../"+FKdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the $nudirK to the FKdir
f.write("os.chdir(\""+basedir+"/"+mydir+"/"+nudirF+"\")\n")           
f.write("for tempf in os.listdir(os.getcwd()):\n\t")
f.write("if tempf.endswith(('.xvc','.nba','.prj','.sps','.sp','.lpt')):\n\t\t")
if s5run == runon:
	f.write("os.system('ln -sf ../"+nudirF+"/'+tempf+' ../"+FKdir+"/'+tempf)\n\t\t") # this will make the appropriate symlinks of the nushellx stuff from the $nudirF to the FKdir
f.close()
os.system('chmod 755 '+linkpy)

os.chdir('..')
if s123run != s123off and args.flow != 'BARE' and ormanual != or1:
	os.chdir(nudirI)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
	os.chdir(nudirK)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
	os.chdir(nudirKgs)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
	os.chdir(nudirF)
	os.system('ln -sf '+intfile+" "+tagit+".int")
	os.system('ln -sf '+spfile+" "+tagit+".sp")
	os.chdir('..')
if s4run == runon:
	os.chdir(KIdir)
	os.system('ln -sf '+GT1bfile+" "+onebop)
	os.system('ln -sf '+GT2bfile+" "+twobop)
	os.chdir('..')
if s5run == runon:
	os.chdir(FKdir)
	os.system('ln -sf '+GT1bfile+" "+onebop)
	os.system('ln -sf '+GT2bfile+" "+twobop)
	os.chdir('..')
sleep(snoozer)

#----------------------------------- STAGE 1 -----------------------------------

# run nushellx for the initial nucleus, $nucI
s1id    = Zid
nucIans = nucI+'.ans'
nucIao  = nucIans+'.o'

if s1run == runon:
	os.chdir(nudirI)
	if args.flow != 'BARE' and ormanual != or1:
		write_ans(nucI,neigI,tagit,tagit,args.ZI,args.A,0,maxJI,delJI,0)
	else:
		write_ans(nucI,neigI,args.sp,args.int,args.ZI,args.A,0,maxJI,delJI,0)
	os.chdir('..')
	sleep(snoozer)

#----------------------------------- STAGE 2 -----------------------------------


# run nushellx for the final nucleus, $nucF
s2id = Zid # stage 2 que id, as a backup...
nucKans = nucK+'.ans'
nucKao  = nucKans+'.o'

if s2run == runon:
	os.chdir(nudirKgs)
	if args.flow != 'BARE' and ormanual != or1:
		write_ans(nucK,'1',tagit,tagit,args.ZI,args.A,0,gsJK,gsJK,0)
	else:
		write_ans(nucK,'1',args.sp,args.int,args.ZI,args.A,0,gsJK,gsJK,0)
	os.chdir('..')
	sleep(snoozer)

	os.chdir(nudirK)
	if args.flow != 'BARE' and ormanual != or1:
		write_ans(nucK,args.neigK,tagit,tagit,args.ZI,args.A,0,sesJK,sesJK,0)
	else:
		write_ans(nucK,args.neigK,args.sp,args.int,args.ZI,args.A,0,sesJK,sesJK,0)
	os.chdir('..')
	sleep(snoozer)

#----------------------------------- STAGE 3 -----------------------------------

# run nushellx for the initial nucleus, $nucI
s3id    = Zid
nucFans = nucF+'.ans'
nucFao  = nucFans+'.o'

if s3run == runon:
	os.chdir(nudirKgs)
	if args.flow != 'BARE' and ormanual != or1:
		write_ans(nucF,neigF,tagit,tagit,args.ZI,args.A,0,maxJF,delJF,0)
	else:
		write_ans(nucF,neigF,args.sp,args.int,args.ZI,args.A,0,maxJF,delJF,0)
	os.chdir('..')
	sleep(snoozer)


#----------------------------------- STAGE 4 -----------------------------------

# run nutbar to get the < K | \sigma\tau | I > NMEs
s4id      = Zid           #satge 3 que id, as a backup...
outfile4  = "nutbar_tensor0_"+nucK+"0.dat" #this should contain the results :)
nutrun4   = "nutbar_"+nucK+"0" 
nutrun4in = nutrun4+".input"

if s4run == runon:
	os.chdir(KIdir)
	if args.flow != 'BARE' and ormanual != or1:
		write_nutrunin(nucI, nucF, tagit, onebop, twobop, c =sesJK)
	else:
		write_nutrunin(nucI, nucF, args.sp, onebop, twobop)
	os.chdir('..')
sleep(snoozer)


#----------------------------------- STAGE 5 -----------------------------------

# run nutbar to get the < F | \sigma\tau | K > NMEs
s5id      = Zid           #satge 3 que id, as a backup...
outfile5  = "nutbar_tensor0_"+nucF+"0.dat" #this should contain the results :)
nutrun5   = "nutbar_"+nucF+"0" 
nutrun5in = nutrun5+".input"

if s5run == runon:
	os.chdir(FKdir)
	if args.flow != 'BARE' and ormanual != or1:
		write_nutrunin(nucI, nucF, tagit, onebop, twobop)
	else:
		write_nutrunin(nucI, nucF, args.sp, onebop, twobop)
	os.chdir('..')
sleep(snoozer)

#---------------------------------SENDING JOB QUEUE----------------------------------


#Sends the job to qsub, where the executable to be run are in execute.py
command = "'python "+imasms+"execute_M2nu.py "+srun+" "+nucI+" "+" "+nucK+" "+nucF+" "+os.path.dirname(os.path.realpath(__file__))+"'"
submit  = "python "+imasms+"nuqsub.py command "+nucI+" M2nu_"+quni+" "+str(wall)+" "+str(ppn)+" "+str(vmem)+" "+str(nth)
os.system(submit)

#-----------------Write script to copy result into desired directory-------------------
mycppy = 'mycopy.py'
totmyr = imamyr+"M2nu/"+nucI+"/"+mydir

f = open(mycppy, "w")
f.write("os.mkdirs("+imamyr+"+M2nu, exist_ok=True)\n")
f.write("os.mkdirs("+imamyr+"M2nu/"+nucI+", exist_ok=True)\n")
f.write("os.mkdirs("+totmyr+")\n")
f.write("os.mkdirs("+totmyr+"/"+nudirI+")\n")
f.write("os.mkdirs("+totmyr+"/"+nudirKgs+")\n")
f.write("os.mkdirs("+totmyr+"/"+nudirK+")\n")
f.write("os.mkdirs("+totmyr+"/"+nudirF+")\n")
f.write("os.mkdirs("+totmyr+"/"+KIdir+")\n")
f.write("os.mkdirs("+totmyr+"/"+FKdir+")\n")
f.write("os.system(cp "+nudirI+"/"+nucI+"*.lpt "+totmyr+"/"+nudirI+")\n")
f.write("os.system(cp "+nudirKgs+"/"+nucK+"*.lpt "+totmyr+"/"+nudirKgs+")\n")
f.write("os.system(cp "+nudirK+"/"+nucK+"*.lpt "+totmyr+"/"+nudirK+")\n")
f.write("os.system(cp "+nudirF+"/"+nucF+"*.lpt "+totmyr+"/"+nudirF+")\n")
f.write("os.system(cp "+KIdir+"/"+outfile4+" "+totmyr+"/"+KIdir+")\n")
f.write("os.system(cp "+FKdir+"/"+outfile5+" "+totmyr+"/"+FKdir+")\n")
f.write("cp -R sumM2nu_* "+totmyr)  # NOTE: technically none of these will exist until sumM2nu.py is run
f.close()
os.system('chmod 755 '+mycppy)