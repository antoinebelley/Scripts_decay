import os
import argparse
from time import sleep

parser = argparse.ArgumentParser()
parser.add_argument("nucI",    help = "Initial nucleus" )
parser.add_argument("nucK",    help = "Intermediate nucleus")
parser.add_argument("nucF",    help = "Initial nucleus" )
parser.add_argument("mydir",   help = "Directory for the run")
parser.add_argument('-m','--mec', action='store_true', default = False, help ='Find a GT operator with meson exchange currents (MECs)')
parser.add_argument('-IF','--inducedforce', action='store_true', default = False, help ='Find a GT operator with induced force (MECs)')
args = parser.parse_args()



#If you change any of these make sure that they match with the names in goM2nu.py
nudirI       = 'nushxI_data'      # this directory will hold the nushellx data for $nucI
nudirKgs     = 'gs_nushxK_data'   # " " " " " " " " the ground state of $nucK
nudirK       = 'nushxK_data'      # " " " " " " " " $nucK
nudirF       = 'nushxF_data'      # " " " " " " " " $nucF
linkdir      = 'nushx_symlinks'   # this directory just holds the symlinks script and output from its clutser run
KIdir        = 'KI_nutbar'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdir        = 'FK_nutbar'        #" " " " " < F | \sigma\tau | K > " "
KIdirHF      = 'KI_nutbar_HF'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdirHF      = 'FK_nutbar_HF'        #" " " " " < F | \sigma\tau | K > " "
KIdirMec     = 'KI_nutbar_Mec'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdirMec     = 'FK_nutbar_Mec'        #" " " " " < F | \sigma\tau | K > " "
KIdirIF      = 'KI_nutbar_If'        # this director will hold the < K | \sigma\tau | i > nutbar results
FKdirIF      = 'FK_nutbar_If'        #" " " " " < F | \sigma\tau | K > " "

if os.environ['HOSTNAME'] == 'oak.arc.ubc.ca':
  PWD = "/global/scratch/belley/M2vu/"
elif str(os.environ['HOSTNAME'])[7:] == "cedar.computecanada.ca" :
  PWD = '/home/belleya/scratch/belleya/M2nu/'
else:
  PWD = '/home/belleya/scratch/belleya/M2nu/'



linkpy    = "./"+linkdir+".py" 
nutrun4   = "nutbar_"+args.nucK+"0" 
nutrun4in = nutrun4+".input"
nutrun5   = "nutbar_"+args.nucF+"0" 
nutrun5in = nutrun5+".input"
bat_s1     = "./"+args.nucI+".bat"
bat_s2_gs  = "./"+args.nucK+".bat"
bat_s2_ses = "./"+args.nucK+".bat"
bat_s3     = "./"+args.nucF+".bat"


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
  os.chdir("..")

def execute_stage2():
  #Run nushell for the intermediate state (both gs and ses)
  os.chdir(nudirKgs)
  os.system(command(bat_s2_gs))
  os.chdir('..')
  os.chdir(nudirK)
  os.system(command(bat_s2_ses))
  os.chdir('..')

def execute_stage3():
  #Run nushell for the final stage
  os.chdir(nudirF)
  os.system(command(bat_s3))
  os.chdir('..')

def execute_links():
  #Run linkpy, dependant on how I run nushellx
  os.chdir(linkdir)
  os.system(command(linkpy))
  os.chdir('..')

def execute_stage4():
  #Run nutbar for Intermediate-Initial step
  os.chdir(KIdir)
  os.system(command(nutrun4in))
  os.chdir('..')
  os.chdir(KIdirHF)
  os.system(command(nutrun4in))
  os.chdir('..')
  if args.mec == True:
    os.chdir(KIdirMec)
    os.system(command(nutrun4in))
    os.chdir('..')
  if args.inducedforce == True:
    os.chdir(KIdirMec)
    os.system(command(nutrun4in))
    os.chdir('..')
    os.chdir(KIdirIF)
    os.system(command(nutrun4in))
    os.chdir('..')
    

def execute_stage5():
  #Run nutbar for Final-intermediate step
  os.chdir(FKdir)
  os.system(command(nutrun5in))
  os.chdir('..')
  os.chdir(FKdirHF)
  os.system(command(nutrun5in))
  os.chdir('..')
  if args.mec == True:
    os.chdir(FKdirMec)
    os.system(command(nutrun5in))
    os.chdir('..')
    os.chdir(FKdirIF)
    os.system(command(nutrun5in))
    os.chdir('..')
  if args.inducedforce == True:
    os.chdir(FKdirMec)
    os.system(command(nutrun5in))
    os.chdir('..')
    os.chdir(FKdirIF)
    os.system(command(nutrun5in))
    os.chdir('..')
    

os.chdir(PWD+args.nucI+"/"+args.mydir+"/")
execute_stage1()
sleep(1)
execute_stage2()
sleep(1)
execute_stage3()
sleep(1)
execute_links()
sleep(1)
execute_stage4()
sleep(1)
execute_stage5()
sleep(1)
os.system('rm -f execute_M2nu.sh')
