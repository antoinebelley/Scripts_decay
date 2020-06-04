import glob
import shutil
import re
import stat
import weakref
from get_nme.Nucl import nushell2snt, sys_kshell #TransitionDensity
import os
import sys
import subprocess
HOME=os.path.expanduser("~")
sys.path.append(HOME)
path_to_kshell=HOME+"/projects/def-holt/shared/KSHELL/version-2019-08-15/"
from time import sleep

if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
  imasms = '/global/home/belley/Scripts_decay/'                           # ' ' ' ' ' ' ReadWrite.py script lives
  imamyr ='/global/home/belley/imsrg/work/results/'                       # ' ' ' ' ' ' final results may be copied to
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
  imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # ' ' ' ' ' ' ReadWrite.py script lives
  imamyr = '/home/belleya/projects/def-holt/belleya/imsrg/work/output/'   # ' ' ' ' ' ' final results may be copied to
else:
  print('This cluster is not known')
  print('Exiting...')
  exit(1) 


class Decay():
  """Class containing general information about 0vbb"""
  def __init__(self, Z, A, flow, sp, inter, emax, e3max, hw):
    self.ZI     = Z
    self.A      = A
    self.flow   = flow
    self.sp     = sp
    self.int    = inter
    self.e3max  = e3max
    self.emax   = emax
    self.hw     = hw
    self.decay  = ''
    #Determine termediate and final nucleus
    self.ZF     = Z+2
    ELEM        = ['blank', 'h', 'he',
                   'li', 'be', 'b',  'c',  'n',  'o', 'f',  'ne',
                   'na', 'mg', 'al', 'si', 'p',  's', 'cl', 'ar',
                   'k',  'ca', 'sc', 'ti', 'v',  'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br', 'kr',
                   'rb', 'sr', 'y',  'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te', 'i',  'xe',
                   'cs', 'ba', 'la', 'ce', 'pr', 'nd', 'pm', 'sm'] # an array of elements from Hydrogen (Z=1) to Samarium (Z=62), includes all current 0vbb candidates
    self.nucI   = f'{ELEM[self.ZI]}{A}'
    self.nucF   = f'{ELEM[self.ZF]}{A}'
    #Parameters for KShell
    self.tagit   = 'IMSRG'  # a tag for the symlinks below
    #Path to the output file of the imsrg depnding on the cluster
    #MAKE SURE THIS RESPECT YOUR NAMING CONVENTION AND ARE THE RIGHT LINK FOR YOUR USER
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
      self.imaout = f'/global/home/belley/imsrg/work/output_{self.nucI}/'                       # this must point to where the IMSRG output files live
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
      self.imaout = f'/home/belleya/projects/def-holt/belleya/imsrg/work/output_{self.nucI}_{inter}/'   # this must point to where the IMSRG output files live
    #Listsfor the Nushell/Nutbar folders
    self.nush_list  = []
    self.nut_list   = []
    #Parent directory for this decay
    self.mydir    = self.mydir() 
    self.run_name = f'{self.decay}_{self.flow}_{self.sp}_{self.int}_e{self.emax}_E{self.e3max}_hw{self.hw}'
    #spfile and intfile (Actually string are added in child classes)
    self.spfile   = ''
    self.intfile  = ''

  def mydir(self):
    """Allows to change self.mydir to add the M0nu or M2nu"""
    path          = os.getcwd()
    try:
      mydir       = f'{path}/{self.nucI}/{self.decay}_{self.flow}_{self.BB}_{self.sp}_{self.int}_e{self.emax}_E{self.e3max}_hw{self.hw}_neig{self.neigK}'
    except AttributeError:
      mydir       = f'{path}/{self.nucI}/{self.decay}_{self.flow}_{self.sp}_{self.int}_e{self.emax}_E{self.e3max}_hw{self.hw}'
    return mydir

  
  def verify_param(self):
    """ Prompt the user to verify the entered parameters"""
    raise NotImplementedError


  def make_directories(self):
    """Creates the required directory where mydir is the dir 
    containing all the others"""
    print('Making the relevant directories...\n\n')
    try:
      shutil.rmtree(self.mydir)#Erase mydir if it already exists
      os.makedirs(self.mydir)
    except:
      os.makedirs(self.mydir)
    for nush in self.k_list:
      os.makedirs(nush.directory)
    for nut in self.NME_list:
      os.makedirs(nut.directory)

  def copy_files(self):
    """Verifies that the .sp and .int file exists and 
    copy them in the directories for nushell, exit otherwise"""
    print('Copying over the relevant files...\n\n')
    name = f'{self.decay}_{self.flow}_{self.sp}_{self.int}_e{self.emax}_E{self.e3max}_hw{self.hw}'
    for dir in self.k_list:
      dir.copy_int_sp(self.intfile, self.spfile, self.imaout)
      os.chdir(dir.directory)
      dir.convert_files(self.spfile,self.intfile, name+'.snt')
      sys_kshell.write_job_kshell(self.ZI, self.A, name)
      for tempf in os.listdir(os.getcwd()):
        if tempf.endswith(('.snt','.sp','.exe')):
          for nut in self.NME_list:
            os.system(f'ln -sf {dir.directory}/{tempf} {nut.directory}/{tempf}')
      os.chdir('..')
    for dir in self.NME_list:
      dir.copy_op(self.imaout)
      os.chdir(dir.directory)
      dir.convert_files(self.spfile, dir.dir+'.snt')
      os.chdir('..')
  
  def write_sh(self):
    raise NotImplementedError

  def send_queue(self, time):
    #Sends the job to qsub, where the executable to be run are in execute.py
    command = self.write_sh()
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
         submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name}'
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name} -m 4000 -t {time} -nd 10'
    os.system(submit)



###########Classes tree that describes the different sub-directories##########
class SubDirectory():
  """Class describing the common attributes 
  of the sub directories inside mydir. Parent to 
  NushellDir and NutbarDir"""
  def __init__(self, directory, mydir):
    self.mydir     = mydir
    self.directory = f'{self.mydir}/{directory}'
    self.dir = directory

  def symlinks(self):
    raise NotImplementedError


class KShellDir(SubDirectory):
  instances = []
  """Class describing the common attributes of a NushellDir"""
  def __init__(self, directory, mydir):
    SubDirectory.__init__(self, directory, mydir)
    self.__class__.instances.append(weakref.proxy(self))

  def copy_int_sp(self, intfile, spfile, path):
    """Copies the sp and int file into the directory"""
    intfile_path   = f'{path}/{intfile}'
    spfile_path    = f'{path}/{spfile}'
    try :
      intfile_path = str(glob.glob(intfile_path)[0])
      spfile_path  = str(glob.glob(spfile_path)[0])
      os.system(f'cp {intfile_path} {spfile_path} {self.directory}')
    except IndexError:
        print('ERROR 5294: cannot find the needed files for KShell!')
        print(f'spfile  = {spfile}')
        print(f'intfile = {intfile}')
        print('Exiting...')
        exit(1)

  def convert_files(self,intfile,spfile,name_out):
    intfile = str(glob.glob(intfile)[0])
    spfile  = str(glob.glob(spfile)[0])
    nushell2snt.scalar(intfile, spfile, name_out)



class NMEDir(SubDirectory):
  instances = []
  """NME dir"""
  def __init__(self, directory, mydir,emax,e3max, outfile, path):
    SubDirectory.__init__(self, directory, mydir)
    self.outfile  = outfile
    self.op1      = ''
    self.op2      = ''
    self.path     = path
    self.directory  = f'{self.directory}'
    self.op1      = f'*e{emax}*E{e3max}*{directory}*_1b.op'
    self.op2      = f'*e{emax}*E{e3max}*{directory}*_2b.op'
    self.__class__.instances.append(weakref.proxy(self))


  def copy_op(self,path):
    """Copies the required op file for nutbar for the decays (ie GT, F, T)"""
    op1b_path        = f'{path}/*{self.op1}'
    op2b_path        = f'{path}/*{self.op2}'
    try :
      op1b_path    = str(glob.glob(op1b_path)[0])
      op2b_path    = str(glob.glob(op2b_path)[0])
      os.system(f'cp {op1b_path} {op2b_path} {self.directory}')
      sleep(1)
    except IndexError:
      if self.flow != 'BARE':
        print('ERROR 3983: cannot find the needed files!')
        print(f'{self.directory} is likely empty')
        print('Exiting...')
        exit(1)

  def convert_files(self,spfile, name_out):
    spfile  = str(glob.glob(spfile)[0])
    op1 = str(glob.glob(self.op1)[0])
    op2 = str(glob.glob(self.op2)[0])
    nushell2snt.tensor(spfile, op1, op2, name_out)

class M0nu(Decay):
  """Class that  contains the methods to obtain M0nu values"""
  # def __init__(self, Z, A, flow, sp, inter, int3N, emax, hw, 
  #              GTbar, Fbar, Tbar):
  def __init__(self, Z, A, flow, sp, inter, emax,e3max, hw):
    Decay.__init__(self, Z, A, flow, sp, inter, emax, e3max, hw)
    self.decay    = 'M0nu'
    self.mydir    = Decay.mydir(self) #Adds the M0nu at the beginning of the one coming from Decay.__init__
    self.run_name = f'{self.decay}_{self.flow}_{self.sp}_{self.int}_e{self.emax}_E{self.e3max}_hw{self.hw}'
    #Create instances of the SubDirectories to add in mydir
    #MAKE SURE THIS RESCPECT THE NAMING CONVENTION`
    #Create NushellDir instances
    self.KShellDir   = KShellDir("Diagonal_space", self.mydir)
    #Name of the nutbar directories and of the associated outfile
    GTdir         = f'GT'
    Fdir          = f'F'
    Tdir          = f'T'
    #Create the instances for the NutbarDir
    self.GTdir    = NMEDir(GTdir, self.mydir, self.emax,self.e3max, "NME_GT.txt", self.imaout)
    self.Fdir     = NMEDir(Fdir, self.mydir, self.emax,self.e3max, "NME_F.txt",  self.imaout)
    self.Tdir     = NMEDir(Tdir, self.mydir, self.emax,self.e3max, "NME_T.txt", self.imaout)
    #Name of the sp, int files  and op base names (wihtout extension)
    self.intfile  = f'*{self.int}*e{self.emax}*E{self.e3max}*.int'
    self.spfile   = f'*{self.int}*e{self.emax}*E{self.e3max}*.sp'
    #Assign the list of the NushellDir and NutbarDir names to the
    #appropriate lists
    self.k_list   = KShellDir.instances 
    self.NME_list = NMEDir.instances

  def verify_param(self):
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('NME       =  M0nu')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'A         =  {self.A}')
    print(f'nucI      =  {self.nucI}')
    print(f'ZI        =  {self.ZI}')
    print(f'nucF      =  {self.nucF}')
    print(f'ZF        =  {self.ZF}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'flow      =  {self.flow}')
    print(f'sp        =  {self.sp}')
    print(f'int       =  {self.int}')
    print(f'emax      =  {self.emax}')
    print(f'e3max     =  {self.e3max}')
    print(f'hw        =  {self.hw}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    incheck = input('Is this input acceptable?(Y/N):')
    print('')
    if incheck == 'n' or incheck == 'N':
      print('Exiting ...')
      exit(1)




  def write_sh(self):
    """Write a bash script to execute execute_M0nu.py"""
    sh = 'execute_m0nu.sh'
    name = f'{self.decay}_{self.flow}_{self.sp}_{self.int}_{self.int3N}_e{self.emax}_hw{self.hw}'   
    f = open(sh, "w")
    f.write('#!/bin/bash\n\n')
    f.write('cd Diagonal_space\n')
    f.write(f'chmod +x {name}_{self.nucI}.sh\n')
    f.write(f'chmod +x {name}_{self.nucF}.sh\n')
    f.write(f'./{name}_{self.nucI}.sh\n')
    f.write(f'./{name}_{self.nucF}.sh\n')
    for dir in self.NME_list:
      f.write(f'ln -sf *.ptn {dir.directory}\n')
      f.write(f'ln -sf *.wav {dir.directory}\n')
    f.write('cd ..\n')
    for dir in self.NME_list:
        f.write(f'cd {dir.directory}\n')
        f.write(f'python {imasms}/get_NME/Nucl/TransitionDensity.py {name}_{dir.dir} {path_to_kshell} {dir.directory} {name}.snt {dir.dir}.snt {name}_{self.nucI}_p.ptn {name}_{self.nucF}_p.ptn {name}_{self.nucI}*.wav {name}_{self.nucF}*.wav \n')
        f.write('cd ..\n')
    f.write(f'rm {sh}\n')
    f.close()
    st = os.stat(sh)
    os.chmod(sh,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )
    return sh
###########################################################################################




