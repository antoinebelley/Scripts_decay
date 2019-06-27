import os
import glob
import shutil
import re
import stat
import weakref
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
  """Class containing general information about 0vbb and 2vbb"""
  def __init__(self, Z, A, flow, sp, inter, int3N, emax, hw):
    self.ZI     = Z
    self.A      = A
    self.flow   = flow
    self.sp     = sp
    self.int    = inter
    self.int3N  = int3N
    self.emax   = emax
    self.hw     = hw
    self.decay  = ''
    #Determine termediate and final nucleus
    self.ZK     = Z+1
    self.ZF     = Z+2
    ELEM        = ['blank', 'h', 'he',
                   'li', 'be', 'b',  'c',  'n',  'o', 'f',  'ne',
                   'na', 'mg', 'al', 'si', 'p',  's', 'cl', 'ar',
                   'k',  'ca', 'sc', 'ti', 'v',  'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br', 'kr',
                   'rb', 'sr', 'y',  'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te', 'i',  'xe',
                   'cs', 'ba', 'la', 'ce', 'pr', 'nd', 'pm', 'sm'] # an array of elements from Hydrogen (Z=1) to Samarium (Z=62), includes all current 0vbb candidates
    self.nucI   = f'{ELEM[self.ZI]}{A}'
    self.nucK   = f'{ELEM[self.ZK]}{A}'
    self.nucF   = f'{ELEM[self.ZF]}{A}'
    #Set values for Nushellx
    self.neigI  = 5        # number of eigenstates for nushellx to calculate for the initial nucelus (I)
    self.maxJI  = 6        # maximum total angular momentum of the initial nucleus' state (I)
    self.delJI  = 1        # step size for the total angular momentum calculations (I) (min = 1 even if maxJI =0)
    self.neigF  = 5        # ...similar to above... (F)
    self.maxJF  = 6        # ...similar to above... (F)
    self.delJF  = 1        # ...similar to above... (F) (min = 1 even if maxJF =0)
    self.tagit   = 'IMSRG'  # a tag for the symlinks below
    #Path to the output file of the imsrg depnding on the cluster
    #MAKE SURE THIS RESPECT YOUR NAMING CONVENTION AND ARE THE RIGHT LINK FOR YOUR USER
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
      self.imaout = f'/global/home/belley/imsrg/work/output_{self.nucI}/'                       # this must point to where the IMSRG output files live
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
      self.imaout = f'/home/belleya/projects/def-holt/belleya/imsrg/work/output_{self.nucI}/'   # this must point to where the IMSRG output files live
    #Listsfor the Nushell/Nutbar folders
    self.nush_list  = []
    self.nut_list   = []
    #Parent directory for this decay
    self.mydir    = self.mydir() 
    #spfile and intfile (Actually string are added in child classes)
    self.spfile   = ''
    self.intfile  = ''

  def mydir(self):
    """Allows to change self.mydir to add the M0nu or M2nu"""
    path          = os.getcwd()
    try:
      mydir       = f'{path}/{self.nucI}/{self.decay}_{self.flow}_{self.BB}_{self.sp}_{self.int}_{self.int3N}_e{self.emax}_hw{self.hw}_neig{self.neigK}'
    except AttributeError:
      mydir       = f'{path}/{self.nucI}/{self.decay}_{self.flow}_{self.sp}_{self.int}_{self.int3N}_e{self.emax}_hw{self.hw}'
    #Directory for the symlink file
    self.linkdir  = f'{mydir}/nushx_symlinks'   # this directory just holds the symlinks script and output from its clutser run
    return mydir
  
  def verify_param(self):
    """ Prompt the user to verify the entered parameters"""
    raise NotImplementedError
  
  def make_directories(self):
    """Creates the required directory where mydir is the dir 
    containing all the others"""
    print('Making the relevant directories...\n\n')
    try:
        os.makedirs(self.mydir)
    except:
        shutil.rmtree(self.mydir)#Erase mydir if it already exists
        os.makedirs(self.mydir)
    os.makedirs(self.linkdir)
    for nush in self.nush_list:
      os.makedirs(nush.directory)
    for nut in self.nut_list:
      os.makedirs(nut.directory)

  def copy_files(self):
    """Verifies that the .sp and .int file exists and 
    copy them in the directories for nushell, exit otherwise"""
    print('Copying over the relevant files...\n\n')
    for dir in self.nush_list:
      dir.copy_int_sp(self.intfile, self.spfile, self.imaout)
    for dir in self.nut_list:
      dir.copy_op(self.imaout)

  def write_linkpy(self):
    """Write a file 'nushx_symplinks.py' to be executed after nushell 
    to create the needed symlinks for nutbar and create symlinks for 
    the int, sp and op files. You should give the op files as argv"""
    #Write linkpy
    print('Prepping all the relevant symlinks...\n\n')
    linkpy = f'{self.linkdir}/nushx_symlinks.py'
    f = open(linkpy,'w')
    f.write('import os\n\n')
    for nush in self.nush_list:
      f.write(f'os.chdir(\'{nush.directory}\')\n')
      f.write('for tempf in os.listdir(os.getcwd()):\n')
      f.write('\tif tempf.endswith((".xvc",".nba",".prj",".sps",".sp",".lpt")):\n')
      for nut in self.nut_list:
        f.write(f'\t\tos.system(f\'ln -sf {nush.directory}/{{tempf}} {nut.directory}/{{tempf}}\')\n') # this will make the appropriate symlinks of the nushellx stuff from the nushdir to the nutdir
    f.close()
    st = os.stat(linkpy)
    os.chmod(linkpy,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH ) #Giives execution right for the file

  def prep_symlinks(self):
    """Creates the symlinks for the sp and int files"""
    self.write_linkpy()
    for dir in self.nush_list:
      if self.flow != 'BARE':
        dir.symlinks(self.tagit, self.intfile, self.spfile)
    for dir in self.nut_list:
      dir.symlinks(self.flow)

  def write_nushell_files(self):
    """Write the nushell files for all the NushellDir"""
    if self.flow != 'BARE':
      sp    = self.tagit
      inter = self.tagit
    else:
      sp    = self.sp
      inter = self.int
    for dir in self.nush_list:
      dir.write_ans(sp,inter, self.A)

  def write_nutbar_files(self):
    if self.flow != 'BARE':
      sp = self.tagit
    else:
      sp = self.sp
    for dir in self.nut_list:
      if dir.step == 'FI':
        dir.write_nutrunin(self.nucI, self.nucF, sp, self.flow)
      elif dir.step == "KI":
        dir.write_nutrunin(self.nucI, self.nucK, sp, self.flow)
      elif dir.step == "FK":
        dir.write_nutrunin(self.nucK, self.nucF, sp, self.flow)

  def write_sh(self):
    raise NotImplementedError

  def send_queue(self):
    raise NotImplementedError


  # def write_copy_results(self):
  #   mycppy    ='mycopies.py' # a script to copy the results to $imamyr
  #   outfileGT ='nutbar_tensor0_'+nucF+'0_'+GTbar+'.dat'
  #   outfileF  ='nutbar_tensor0_'+nucF+'0_'+Fbar+'.dat'
  #   outfileT  ='nutbar_tensor0_'+nucF+'0_'+Tbar+'.dat'
  #   totmyr    = f'{imamyr}{self.decay}/{self.nucI}/{self.mydir}'
  #   f = open(mycppy, 'w')
  #   f.write('import os\n')
  #   f.write(f'os.makedirs("{imamyr}{self.decay}", exist_ok=True)\n')
  #   f.write(f'os.makedirs("{imamyr}{self.decay}/{self.nucI}", exist_ok=True)\n')
  #   f.write(f'os.makedirs("{totmyr}")\n')
  #   for nush in self.nushdir():
  #     f.write(f'os.makedirs("{nush}")')
  #   for nut in self.nutdir():
  #     f.write(f'os.makedirs("{nut}")')



###########Classes tree that describes the different sub-directories##########
class SubDirectory():
  """Class describing the common attributes 
  of the sub directories inside mydir. Parent to 
  NushellDir and NutbarDir"""
  def __init__(self, directory, mydir):
    self.mydir     = mydir
    self.directory = f'{self.mydir}/{directory}'

  def symlinks(self):
    raise NotImplementedError


class NushellDir(SubDirectory):
  instances = []

  """Class describing the common attributes of a NushellDir"""
  def __init__(self, directory, mydir, nucleus, Z, neig, minJ, maxJ, delJ, parity = 0):
    SubDirectory.__init__(self, directory, mydir)
    self.nucleus = nucleus
    self.Z       = Z
    self.neig    = neig
    self.minJ    = minJ
    self.maxJ    = maxJ
    self.delJ    = delJ
    self.parity  = parity
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
      if self.flow != 'BARE':
          print('ERROR 5294: cannot find the needed files for nushellx!')
          print(f'spfile  = {spfile}')
          print(f'intfile = {intfile}')
          print('Exiting...')
          exit(1)

  def symlinks(self, sp, intfile, spfile):
    os.chdir(self.directory)
    os.system(f'ln -sf {intfile} {sp}.int')
    os.system(f'ln -sf {spfile} {sp}.sp')
    os.chdir(self.mydir)

  def write_ans(self, sp, inter, A):
    """Writes the ans file for nushell and compile it 
       sending the output to the ans.o file"""
    nucans      = f'{self.nucleus}.ans'
    nucans_path = f'{self.directory}/{nucans}'
    nucao       = f'{nucans}.o'
    f = open(nucans_path,'w') #Wil overwrite file if they already exists
    f.write('--------------------------------------------------\n')
    f.write(f'lpe,   {self.neig}             ! option (lpe or lan), neig (zero=10)\n')
    f.write(f'{sp}                ! model space (*.sp) name (a8)\n')
    f.write('n                    ! any restrictions (y/n)\n')
    f.write(f'{inter}                ! model space (*.int) name (a8)\n')
    f.write(f' {self.Z}                  ! number of protons\n')
    f.write(f' {A}                  ! number of nucleons\n')
    f.write(f' {self.minJ}.0, {self.maxJ}.0, {self.delJ}.0,      ! min J, max J, del J\n')
    f.write(f'  {self.parity}                  ! parity (0 for +) (1 for -) (2 for both)\n')
    f.write('--------------------------------------------------\n')
    f.write('st                   ! option\n')
    f.close()
    print(f'Setting up {nucans} for nushellx...')
    os.chdir(self.directory)
    os.system(f'shell {nucans} >> {nucao}') # set up files for nushellx, and divert stdout to file
    sleep(1)
    os.chdir(self.mydir)
    st = os.stat(f'{self.directory}/{self.nucleus}.bat')
    os.chmod(f'{self.directory}/{self.nucleus}.bat',st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )



class NutbarDir(SubDirectory):
  """Class describing the common attributes of a NutbarlDir
  Parrent to NutbarDirM0nu and NutbarDirM2nu"""
  def __init__(self, directory, mydir, filebase, outfile, step, JI=0, NI=1, JF=0, NF=1):
    SubDirectory.__init__(self,directory, mydir)
    self.outfile  = outfile
    self.op1      = ''
    self.op2      = ''
    self.step     = step #ie FI, FK or KI
    self.JI       = JI
    self.NI       = NI
    self.JF       = JF
    self.NF       = NF
    #This the string to find the op files
    #For the M0nu it is the barcode
    #For the M2nu it is the filebase
    self.filebase = filebase
    

  def symlinks(self, flow):
    #The name of the symlinks to the operator files
    onebop = flow+"_M0nu_1b.op" 
    twobop = flow+"_M0nu_2b.op" 
    #Create the symlinks
    os.chdir(self.directory)
    os.system(f'ln -sf *{self.op1} {onebop}')
    os.system(f'ln -sf *{self.op2} {twobop}')
    os.chdir(self.mydir)

  def write_nutrunin(self, nucI, nucF, sp, flow):
    """Write the input file for nutbar"""
    nutrun   = f'{self.directory}/nutbar_{nucF}0' 
    nutrunin = f'{nutrun}.input'
    onebop = flow+"_M0nu_1b.op" 
    twobop = flow+"_M0nu_2b.op" 
    f = open(nutrunin,'w')
    f.write(f'{sp}\n')
    if len(nucI)==3:
        nucIsplit = list(nucI)
        nucI = f'{nucIsplit[0]}_{nucIsplit[1]}{nucIsplit[2]}'
    if len(nucF)==3:
        nucFsplit = list(nucF)
        nucF = f'{nucFsplit[0]}_{nucFsplit[1]}{nucFsplit[2]}'
    f.write(f'{nucI}0\n')
    f.write(f'{nucF}0\n')
    f.write(f'{onebop} {twobop}\n')
    f.write(f'{self.JI}.0\n')
    f.write(f'{self.NI}\n')
    f.write(f'{self.JF}.0\n')
    f.write(f'{self.NF}\n\n')
    f.close()

  def copy_op(self):
    raise NotImplementedError



class NutbarDirM0nu(NutbarDir):
  """Class describing the common attributes of 
  a NutbarlDir of the 0vbb"""
  instances = []
  def __init__(self, directory, mydir, barcode, outfile, step, path, JI=0, NI=1, JF=0, NF=1):
    NutbarDir.__init__(self, directory, mydir, barcode, outfile, step, JI, NI, JF, NF)
    self.path     = path
    self.barcode  = self.timeit(barcode)
    self.directory    = f'{self.directory}{self.barcode}'
    self.op1      = f'*{self.barcode}_1b.op'
    self.op2      = f'*{self.barcode}_2b.op'
    self.header   = f'M0nu_header_{self.barcode}.txt'
    self.__class__.instances.append(weakref.proxy(self))

  def timeit(self, barcode):
    """Get a timestamp when given a M0nu barcode"""
    try:
        timestamp = str(glob.glob(f'{self.path}/M0nu_header_{barcode}*.txt')[0])
        timestamp = re.sub(f'{self.path}M0nu_header_', '', timestamp)
        timestamp = re.sub('.txt', '', timestamp)
        return timestamp
    except IndexError: 
        print('ERROR 2135: cannot find a barcode!')
        print(f'{barcode} was not found')
        print('Exiting...')
        exit(1)

  def copy_op(self,path):
    """Copies the required op file for nutbar for the decays (ie GT, F, T)"""
    op1b_path        = f'{path}/*{self.barcode}_1b.op'
    op2b_path        = f'{path}/*{self.barcode}_2b.op'
    header_path      = f'{path}/{self.header}'
    try :
        op1b_path    = str(glob.glob(op1b_path)[0])
        op2b_path    = str(glob.glob(op2b_path)[0])
        header_path  = str(glob.glob(header_path)[0])
        os.system(f'cp {op1b_path} {op2b_path} {self.directory}')
        sleep(1)
        os.system(f'cp {header_path} {self.mydir}')
        sleep(1)
    except IndexError:
        if self.flow != 'BARE':
            print('ERROR 3983: cannot find the needed files!')
            print(f'{self.directory} is likely empty')
            print('Exiting...')
            exit(1)


class NutbarDirM2nu(NutbarDir):
  """Class describing the common attributes of 
  a NutbarlDir of the 2vbb"""
  instances = []
  def __init__(self, directory, mydir, filebase, outfile, step, JI=0, NI=1, JF=0, NF=1, MEC = False):
    NutbarDir.__init__(self, directory, mydir, filebase, outfile, step, JI, NI, JF, NF)
    self.__class__.instances.append(weakref.proxy(self))
    if MEC == True:
      self.op1 = f'{self.filebase}MEC_GTMEC_1b.op'
      self.op2 = f'{self.filebase}MEC_GTMEC_2b.op'
    else:
      self.op1 = f'{self.filebase}_GamowTeller_1b.op'
      self.op2 = f'{self.filebase}_GamowTeller_2b.op'

  def copy_op(self, path):
    """Copies the required file op for nutbar"""
    op1b_path        = f'{path}{self.op1}'
    op2b_path        = f'{path}{self.op2}'
    try :
      op1b_path    = str(glob.glob(op1b_path)[0])
      op2b_path    = str(glob.glob(op2b_path)[0])
      os.system(f'cp {op1b_path} {op2b_path} {self.directory}')
    except IndexError:
        print('ERROR 3983: cannot find the needed files!')
        print(f'{self.directory} is likely empty')
        print('Exiting...')
        exit(1)
###############################################################################


class M0nu(Decay):
  """Class that  contains the methods to obtain M0nu values"""
  def __init__(self, Z, A, flow, sp, inter, int3N, emax, hw, 
               GTbar, Fbar, Tbar):
    Decay.__init__(self, Z, A, flow, sp, inter, int3N, emax, hw)
    self.decay    = 'M0nu'
    self.mydir    = Decay.mydir(self) #Adds the M0nu at the beginning of the one coming from Decay.__init__
    self.run_name = f'{self.decay}_{self.flow}_{self.sp}_{self.int}_{self.int3N}_e{self.emax}_hw{self.hw}'
    #Create instances of the SubDirectories to add in mydir
    #MAKE SURE THIS RESCPECT THE NAMING CONVENTION`
    #Create NushellDir instances
    self.nudirI   = NushellDir('nushxI_data', self.mydir, self.nucI, self.ZI, self.neigI, 0, self.maxJI, self.delJI)
    self.nudirF   = NushellDir('nushxF_data', self.mydir, self.nucF, self.ZF, self.neigF, 0, self.maxJF, self.delJF)
    #Name of the nutbar directories and of the associated outfile
    GTdir         = f'GT_'
    Fdir          = f'F_'
    Tdir          = f'T_'
    outfile       = f'nutbar_tensor0_{self.nucF}0.dat'
    #Create the instances for the NutbarDir
    self.GTdir    = NutbarDirM0nu(GTdir, self.mydir, GTbar, outfile, 'FI', self.imaout)
    self.Fdir     = NutbarDirM0nu(Fdir, self.mydir, Fbar, outfile, 'FI', self.imaout)
    self.Tdir     = NutbarDirM0nu(Tdir, self.mydir, Tbar, outfile, 'FI', self.imaout)
    #Name of the sp, int files  and op base names (wihtout extension)
    self.intfile  = f'*{self.GTdir.barcode}.int'
    self.spfile   = f'*{self.GTdir.barcode}.sp'
    #Assign the list of the NushellDir and NutbarDir names to the
    #appropriate lists
    self.nush_list = NushellDir.instances
    self.nut_list  = NutbarDirM0nu.instances

  def verify_param(self):
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('NME       =  M0nu')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'A         =  {self.A}')
    print(f'nucI      =  {self.nucI}')
    print(f'ZI        =  {self.ZI}')
    print(f'neigI     =  {self.neigI}')
    print(f'maxJI     =  {self.maxJI}')
    print(f'delJI     =  {self.delJI}')
    print(f'nucF      =  {self.nucF}')
    print(f'ZF        =  {self.ZF}')
    print(f'neigF     =  {self.neigF}')
    print(f'maxJF     =  {self.maxJF}')
    print(f'delJF     =  {self.delJF}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'flow      =  {self.flow}')
    print(f'sp        =  {self.sp}')
    print(f'int       =  {self.int}')
    print(f'int3N     =  {self.int3N}')
    print(f'emax      =  {self.emax}')
    print(f'hw        =  {self.hw}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'GTbar     =  {self.GTdir.barcode}')
    print(f'Fbar      =  {self.Fdir.barcode}')
    print(f'Tbar      =  {self.Tdir.barcode}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    incheck = input('Is this input acceptable?(Y/N):')
    print('')
    if incheck == 'n' or incheck == 'N':
      print('Exiting ...')
      exit(1)

  def write_sh(self):
    """Write a bash script to execute execute_M0nu.py"""
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
        file = '/global/home/belley/Scripts_decay/execute_M0nu.py'
        sh   = '/global/home/belley/Scripts_decay/execute_M0nu.sh'
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        file = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute0.py'
        sh   = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M0nu.sh'
    else:
        print('This cluster is not known')
        print('Add the paths to execute_M0nu.py in this cluster')
        print('Exiting...')
        exit(1)     
    f = open(sh, "w")
    f.write('#!/bin/bash\n\n')
    f.write('chmod +x '+file+'\n')
    f.write(f'python {file} {self.nucI} {self.nucF} {self.GTdir.barcode} {self.Fdir.barcode} {self.Tdir.barcode} {self.run_name}')
    f.close()
    st = os.stat(sh)
    os.chmod(sh,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )
    return sh

  def send_queue(self, time):
    #Sends the job to qsub, where the executable to be run are in execute.py
    command = self.write_sh()
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
         submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name}'
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name} -t {time}'
    os.system(submit)
###########################################################################################

class M2nu(Decay):
  """Class that  contains the methods to obtain M2nu values"""
  def __init__(self, Z, A, flow, sp, inter, int3N, emax, hw, 
               neigK, BB, MEC = False):
    Decay.__init__(self, Z, A, flow, sp, inter, int3N, emax, hw)
    #Value for to use in Nushell for the intermediate state
    self.maxJK    = 6
    self.delJK    = 1         #(min = 1 even if maxJI =0)
    self.get_JK()
    self.neigK    = neigK
    self.BB       = BB
    self.decay    = 'M2nu'
    self.mydir    = Decay.mydir(self) #Adds the M2nu at the beginning of the one coming from Decay.__init__()
    if MEC == True:
      self.mydir = f'{self.mydir}_MEC'
    self.MEC      = MEC
    self.run_name = f'{self.decay}_{self.flow}_{self.BB}_{self.sp}_{self.int}_{self.int3N}_e{self.emax}_hw{self.hw}_neig{self.neigK}'
    #PATH TO THE SP AND INT FILES
    #The sp files and int files have an arbritary phase
    #Since we add the result for the MEC to the normal IMSRG result
    #in sumM2nu.py afterwards, the two calculations need to have the
    #same phase so we need to take the same int and sp files for them.
    #Also, to reproduce FIG 14 of arXiv:1903.00047, we need the M0nu for
    #the HF operator with the IMSRG operator so we also need the same
    #int and sp files for the HF operator
    #The following scheme insures that is the case
    #(go see output of IMSRG to convince yourself)
    if self.flow == 'BARE':
      filebase = f'*{self.flow}*{self.BB}*'
    elif self.int == 'magic':
      filebase_int = f'*{self.int}*3N*'
      filebase     = f'*{self.int}*{self.BB}*'
    else:
      filebase = f'*{self.BB}*{self.int}*'
    self.filebase = f'{filebase}e{self.emax}*hw{self.hw}*A{self.A}*forM2nu'
    self.intfile  = f'{filebase_int}e{self.emax}*hw{self.hw}*A{self.A}*forM2nu_.int'
    self.spfile   = f'{filebase_int}e{self.emax}*hw{self.hw}*A{self.A}*forM2nu_.sp'
    #Create instances of the SubDirectories to add in mydir
    #MAKE SURE THIS RESCPECT THE NAMING CONVENTION`
    #Ceate NushellDir instances
    self.nudirI   = NushellDir('nushxI_data', self.mydir, self.nucI, self.ZI, self.neigI, 0, self.maxJI, self.delJI)
    self.nudirF   = NushellDir('nushxF_data', self.mydir, self.nucF, self.ZF, self.neigF, 0, self.maxJF, self.delJF)
    self.nudirKgs = NushellDir('gs_nushxK_data', self.mydir, self.nucK, self.ZK, 1, 0, self.gsJK, self.gsJK, self.gsPK)
    self.nudirK   = NushellDir('nushxK_data', self.mydir, self.nucK, self.ZK, self.neigK, 0, self.sesJK, self.sesJK, self.sesPK)
    #Create the NutBarDir instances
    outfileKI  = f'nutbar_tensor1_{self.nucK}0.dat'
    outfileFK  = f'nutbar_tensor1_{self.nucF}0.dat'
    self.KIdir    = NutbarDirM2nu(directory ='KI_nutbar', mydir = self.mydir, filebase = self.filebase, outfile = outfileKI, step ='KI', JF=self.sesJK, NF=self.neigK, MEC = MEC)
    self.FKdir    = NutbarDirM2nu(directory ='FK_nutbar', mydir = self.mydir, filebase = self.filebase, outfile = outfileFK, step ='FK', JI=self.sesJK, NI=self.neigK, MEC = MEC)
    #Assign the list of the NushellDir and NutbarDir names to the
    #appropriate lists
    self.nush_list = NushellDir.instances
    self.nut_list  = NutbarDirM2nu.instances
    

  def get_JK(self):
    if self.nucK == 'sc48':
      self.gsJK=6
      self.gsPK=0
      self.sesJK=1 # the total angular momentum of the intermediate nuclear excited states (to be summed over)
      self.sesPK=0 # the parity of the " " " " " " " ", 0 = positive, 1 = negative
    else:
      print('ERROR 0429: the intermediate g.s./s.e.s. for this decay has not been set, please add them to the g.s./s.e.s. if-else ladder in M2nu.get_JK()!') 
      print(f'nucK = {self.nucK}')
      print('Exiting...')
      exit(1)

  def verify_param(self):
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('NME       =  M2nu')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'MEC  =  {self.MEC}')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'A         =  {self.A}')
    print(f'nucI      =  {self.nucI}')
    print(f'ZI        =  {self.ZI}')
    print(f'neigI     =  {self.neigI}')
    print(f'maxJI     =  {self.maxJI}')
    print(f'delJI     =  {self.delJI}')
    print(f'nucK      =  {self.nucK}')
    print(f'ZK        =  {self.ZK}')
    print(f'neigI     =  {self.neigK}')
    print(f'maxJI     =  {self.maxJK}')
    print(f'delJI     =  {self.delJK}')
    print(f'nucF      =  {self.nucF}')
    print(f'ZF        =  {self.ZF}')
    print(f'neigF     =  {self.neigF}')
    print(f'maxJF     =  {self.maxJF}')
    print(f'delJF     =  {self.delJF}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'flow      =  {self.flow}')
    print(f'BB        =  {self.BB}')
    print(f'sp        =  {self.sp}')
    print(f'int       =  {self.int}')
    print(f'int3N     =  {self.int3N}')
    print(f'emax      =  {self.emax}')
    print(f'hw        =  {self.hw}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(f'gsJK      =  {self.gsJK}')
    print(f'gsPK      =  {self.gsPK}')
    print(f'sesJK     =  {self.sesJK}')
    print(f'sesPK     =  {self.sesPK}')
    print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    incheck = input('Is this input acceptable?(Y/N):')
    print('')
    if incheck == 'n' or incheck == 'N':
      print('Exiting ...')
      exit(1)

  def write_sh(self):
    """Write a bash script to execute execute_M2nu.py"""
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
      file = '/global/home/belley/Scripts_decay/execute_M2nu.py'
      sh   = '/global/home/belley/Scripts_decay/execute_M2nu.sh'
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
      file = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute2.py'
      sh   = '/home/belleya/projects/def-holt/belleya/Scripts_decay/execute_M2nu.sh'
    else:
      print('This cluster is not known')
      print('Add the paths to execute_M2nu.py in this cluster')
      print('Exiting...')
      exit(1)
    f = open(sh, 'w')
    f.write('#!/bin/bash\n\n')
    f.write(f'chmod +x {file}\n')
    f.write(f'python {file} {self.nucI} {self.nucK} {self.nucF} {self.run_name}')
    f.close()
    st = os.stat(sh)
    os.chmod(sh,st.st_mode |stat.S_IXUSR| stat.S_IXGRP|stat.S_IXOTH )
    return sh

  def send_queue(self, time):
    #Sends the job to qsub, where the executable to be run are in execute.py
    command = self.write_sh()
    if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
         submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name}'
    elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
        submit  = f'python {imasms}nuqsub.py {command} {self.nucI} {self.run_name} -t {time}'
    os.system(submit)