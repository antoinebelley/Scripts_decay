import pandas as pd
import sys
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
#Append the path to the modules and import them. 
#Make sure those are the right path for your user
if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
  imasms = '/global/home/belley/Scripts_decay/'                           # ' ' ' ' ' ' nuqsub.py script lives
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
  imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # ' ' ' ' ' ' nuqsub.py script lives
else:
  print('This cluster is not known')
  print('Add the paths to execute_M2nu.py in this cluster')
  print('Exiting...')
  exit(1)
sys.path.append(imasms)
from ReadWrite import *
from decay import M2nu

class DataM2nu():

  def __init__(self, Z, A, emax, hw, neigK, shift, correction):
    self.ZI          = Z
    self.A           = A
    self.emax        = emax
    self.hw          = hw
    self.neigK       = neigK
    self.shift       = shift
    self.correction  = correction
    self.name        = f'emax{self.emax}_hw{self.hw}_{self.shift}_{self.correction}'
    #Determine the intermediate and final nucleus
    self.ZK          = Z+1
    self.ZF          = Z+2
    self.ELEM = ['blank', 'h', 'he',
                'li', 'be', 'b',  'c',  'n',  'o', 'f',  'ne',
                'na', 'mg', 'al', 'si', 'p',  's', 'cl', 'ar',
                'k',  'ca', 'sc', 'ti', 'v',  'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br', 'kr',
                'rb', 'sr', 'y',  'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te', 'i',  'xe',
                'cs', 'ba', 'la', 'ce', 'pr', 'nd', 'pm', 'sm'] # an array of elements from Hydrogen (Z=1) to Samarium (Z=62), includes all current 0vbb candidates
    self.nucI        = f'{self.ELEM[self.ZI]}{A}'
    self.nucK        = f'{self.ELEM[self.ZK]}{A}'
    self.nucF        = f'{self.ELEM[self.ZF]}{A}'
    #Find the path (and make sure that it exists) 
    #to the directory for the BARE, SRG and MEC results
    Gx1apnDir   = f'{self.nucI}/M2nu*_OS_*e{self.emax}*hw{self.hw}*neig{self.neigK}'
    SigmaTauDir = f'{self.nucI}/M2nu*_HF_*e{self.emax}*hw{self.hw}*neig{self.neigK}'
    SrgDir      = f'{self.nucI}/M2nu*_3N_*e{self.emax}*hw{self.hw}*neig{self.neigK}'
    MecDir      = f'{self.nucI}/M2nu*_3N_*e{self.emax}*hw{self.hw}*neig{self.neigK}_MEC'
    directories = [Gx1apnDir, SigmaTauDir, SrgDir, MecDir]
    for directory in directories:
      try:
        directory = glob.glob(f'{directory}')[0]
      except IndexError:
        print(f'ERROR: Cannot find {directory}')
        print('Exiting...')
        exit(1)
    self.Gx1apnDir   = glob.glob(f'{Gx1apnDir}')[0]
    self.SigmaTauDir = glob.glob(f'{SigmaTauDir}'[0])
    self.SrgDir      = glob.glob(f'{SrgDir}')[0]
    self.MecDir      = glob.glob(f'{MecDir}')[0]
    #Make sure those are the same then in goM2nu.py
    self.KIdir    = 'KI_nutbar'
    self.FKdir    = 'FK_nutbar'
    self.nudirI   = 'nushxI_data'
    self.nudirKgs = 'gs_nushxK_data'
    self.nudirK   = 'nushxK_data'
    self.nudirF   = 'nushxF_data'
    self.nutfileK  = f'nutbar_tensor1_{self.nucK}0_{self.nucI}0.dat'
    self.nutfileF  = f'nutbar_tensor1_{self.nucF}0_{self.nucK}0.dat'
    #Verify that the nutbar file exists and have the same number of lines
    for directory in directories:
      verify_nutbar(self.nucK, self.nucF, directory, self.KIdir, self.FKdir, self.nutfileK, self.nutfileF)
    #Go get the experimental value of the energie shift and the ExP enrgy of the ground state
    self.EXP, self.Eshift = getEXP(self.shift, self.nucK)
    #Directrory where to write the results
    self.outdir = f'{self.nucI}/results/emax{emax}_hw{hw}'


  def sumM2nu_gx1apn(self):
    """Calculate the M2nu for the OS op with the gx1apn interaction"""
    EKgs = read_Egs(f'{self.nucK}', f'{self.Gx1apnDir}/{self.nudirKgs}')
    M2nu    = 0 # initialize the sum over K
    Cexp    = 0 # initialize the correction value = $EXP - min($EK-$EKgs)
    maxKsum = self.neigK+8
    M2nu_array  = []
    ExC_array   = []
    for i in range(7,maxKsum-1):
      EK, nmeKI = read_Eses(state = i, directory = f'{self.Gx1apnDir}/{self.KIdir}', file = self.nutfileK)
      EF, nmeFK = read_Eses(state = i, directory = f'{self.Gx1apnDir}/{self.FKdir}', file = self.nutfileF)
      Ex        = EK-EKgs                           # the excitation energy     
      if self.correction == 'on' and i == 7:
          Cexp = self.EXP - Ex                         # the experimental energy correction value
      ExC   = Ex+Cexp
      denom = ExC+self.Eshift                    # denominator of the sum
      M2nu  = single_M2nu(nmeKI, nmeFK, M2nu,denom)
      aM2nu = abs(M2nu)
      M2nu_array.append(aM2nu)
      ExC_array.append(ExC)
    M2nu_array = np.array(M2nu_array)
    ExC_array  = np.array(ExC_array)
    self.M2nu    = M2nu_array
    self.M2nuQ82 = self.M2nu*0.82*0.82
    self.M2nuQ77 = self.M2nu*0.77*0.77
    self.M2nuQ74 = self.M2nu*0.74*0.74
    self.ExC     = ExC_array

  def sumM2nu_sigmatau(self):
    """Caculate the sum for the sigma tau HF op with the imsrg wave function"""
    EKgs = read_Egs(f'{self.nucK}', f'{self.Gx1apnDir}/{self.nudirKgs}')
    M2nu    = 0 # initialize the sum over K
    Cexp    = 0 # initialize the correction value = $EXP - min($EK-$EKgs)
    maxKsum = self.neigK+8
    M2nu_array  = []
    ExC_array   = []
    for i in range(7,maxKsum-1):
      EK, nmeKI = read_Eses(state = i, directory = f'{self.SigmaTauDir}/{self.KIdir}', file = self.nutfileK)
      EF, nmeFK = read_Eses(state = i, directory = f'{self.SigmaTauDir}/{self.FKdir}', file = self.nutfileF)
      Ex        = EK-EKgs                           # the excitation energy     
      if self.correction == 'on' and i == 7:
          Cexp = self.EXP - Ex                         # the experimental energy correction value
      ExC   = Ex+Cexp
      denom = ExC+self.Eshift                    # denominator of the sum
      M2nu  = single_M2nu(nmeKI, nmeFK, M2nu,denom)
      aM2nu = abs(M2nu)
      M2nu_array.append(aM2nu)
    M2nu_array   = np.array(M2nu_array)
    self.M2nuSig = M2nu_array

  def sumM2nu_evolved(self):
    EKgs     = read_Egs(f'{self.nucK}', f'{self.SrgDir}/{self.nudirKgs}')
    M2nu     = 0 # initialize the sum over K
    M2nu_MEC = 0 # """""
    Cexp     = 0 # initialize the correction value = $EXP - min($EK-$EKgs)
    maxKsum  = self.neigK+8
    M2nu_array      = []
    M2nu_array_MEC  = []
    factor = -3.419935
    for i in range(7,maxKsum-1):
      EK, nmeKI = read_Eses(state = i, directory = f'{self.SrgDir}/{self.KIdir}', file = self.nutfileK)
      EF, nmeFK = read_Eses(state = i, directory = f'{self.SrgDir}/{self.FKdir}', file = self.nutfileF)
      Ex      = EK-EKgs                           # the excitation energy     
      if self.correction == 'on' and i == 7:
          Cexp = self.EXP - Ex                         # the experimental energy correction value
      denom   = Ex+Cexp+self.Eshift                    # denominator of the sum
      M2nu = single_M2nu(nmeKI, nmeFK, M2nu,denom)
      aM2nu  = abs(M2nu)
      M2nu_array.append(aM2nu)
      #Calculate for MEC where nmeKI = nmeKISRG-nmeKIMEC and similar for nmeFK
      KIdir_MEC = f'{self.MecDir}/{self.KIdir}'
      FKdir_MEC = f'{self.MecDir}/{self.FKdir}'
      EK_MEC, nmeKI_MEC = read_Eses(state = i, directory = KIdir_MEC, file = self.nutfileK)
      EF_MEC, nmeFK_MEC = read_Eses(state = i, directory = FKdir_MEC, file = self.nutfileF)
      nmeKI_MEC *= factor
      nmeFK_MEC *= factor
      nmeKI_MEC = nmeKI+nmeKI_MEC
      nmeFK_MEC = nmeFK+nmeFK_MEC
      M2nu_MEC  = single_M2nu(nmeKI_MEC, nmeFK_MEC, M2nu_MEC, denom)
      aM2nu_MEC = abs(M2nu_MEC)
      M2nu_array_MEC.append(aM2nu_MEC)
    M2nu_array = np.array(M2nu_array)
    M2nu_array_MEC = np.array(M2nu_array_MEC)
    self.M2nuMec = M2nu_array_MEC
    self.M2nuSrg = M2nu_array

  def getdataframe(self):
    try :
      data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.sigma, self.M2nuSrg, self.M2nuMec])
    except AttributeError:
      self.sumM2nu_gx1apn()
      try:
        data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.sigma, self.M2nuSrg, self.M2nuMec])
      except AttributeError:
        self.sumM2nu_evolved()
        try:
          data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.sigma self.M2nuSrg, self.M2nuMec])
        except AttributeError:
          self.sumM2nu_sigmatau()
          data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.sigma self.M2nuSrg, self.M2nuMec])
    data = pd.DataFrame(data.transpose())
    data.columns = ['ExC', 'Gx1apn','qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec']
    self.data = data

  def write_plot_file(self):
    plotfile = f'plot_{self.name}.dat'
    try:
      self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                      'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec'], index=False)
    except:
      self.getdataframe()
      self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                      'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec'], index=False)
  
  def write_output_file(self):
    EIgs = read_Egs(f'{self.nucI}', f'{self.Gx1apnDir}/{self.nudirI}')
    EKgs = read_Egs(f'{self.nucK}', f'{self.Gx1apnDir}/{self.nudirKgs}')
    EFgs = read_Egs(f'{self.nucF}', f'{self.Gx1apnDir}/{self.nudirF}')
    EIgsSrg = read_Egs(f'{self.nucI}', f'{self.SrgDir}/{self.nudirI}')
    EKgsSrg = read_Egs(f'{self.nucK}', f'{self.SrgDir}/{self.nudirKgs}')
    EFgsSrg = read_Egs(f'{self.nucF}', f'{self.SrgDir}/{self.nudirF}')
    EIgsMec = read_Egs(f'{self.nucI}', f'{self.MecDir}/{self.nudirI}')
    EKgsMec = read_Egs(f'{self.nucK}', f'{self.MecDir}/{self.nudirKgs}')
    EFgsMec = read_Egs(f'{self.nucF}', f'{self.MecDir}/{self.nudirF}')
    outfile = f'results_{self.name}.txt'

    f = open(f'{self.outdir}/{outfile}', 'w')
    f.write(f'Shift         =  {self.shift}\n')
    f.write(f'Correction    =  {self.correction}\n')
    f.write(f'nucI          =  {self.nucI}\n')
    f.write(f'nucK          =  {self.nucK}\n')
    f.write(f'nucF          =  {self.nucF}\n')
    f.write(f'Eshift        =  {self.Eshift}\n')
    f.write(f'EXP           =  {self.EXP}\n')
    f.write(f'EIgs          =  {EIgs}\n')
    f.write(f'EKgs          =  {EKgs}\n')
    f.write(f'EFgs          =  {EFgs}\n\n')
    M2nu    = self.M2nu[len(self.M2nu)-1]
    M2nuQ82 = self.M2nuQ82[len(self.M2nu)-1]
    M2nuQ77 = self.M2nuQ77[len(self.M2nu)-1]
    M2nuQ74 = self.M2nuQ74[len(self.M2nu)-1]
    M2nuSig = self.M2nuSig[len(self.M2nu)-1]
    M2nuSrg = self.M2nuSrg[len(self.M2nu)-1]
    M2nuMec = self.M2nuMec[len(self.M2nu)-1]
    f.write('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    f.write('... and the caclulations come to!\n\n')
    f.write(f'M2nu           = {M2nu}\n')
    f.write(f'M2nu*0.82*0.82 = {M2nuQ82}\n')
    f.write(f'M2nu*0.77*0.77 = {M2nuQ77}\n')
    f.write(f'M2nu*0.74*0.74 = {M2nuQ74}\n')
    f.write(f'M2nu(sigtau)   = {M2nu}\n')
    f.write(f'M2nu(SRG)      = {M2nuSrg}\n')
    f.write(f'M2nu(SRG+MEC)  = {M2nuMec}\n')
    f.close()
    self.M2nu_result    = M2nu
    self.M2nuQ82_result = M2nuQ82
    self.M2nuQ77_result = M2nuQ77
    self.M2nuQ74_result = M2nuQ74
    self.M2nuSig_result = M2nuSig
    self.M2nuSrg_result = M2nuSrg
    self.M2nuMec_result = M2nuMec


  def make_plot(self):
    fig = plt.figure()
    plt.plot(self.data['ExC'], self.data['Gx1apn'], label=r'gx1apn$')
    plt.plot(self.data['ExC'], self.data['qf = 0.82'], label='qf=0.82')
    plt.plot(self.data['ExC'], self.data['SigmaTau'], label=r'$\sigma\tau$')
    plt.plot(self.data['ExC'], self.data['Srg'], label=r'$\sigma\tau$(srg)')
    plt.plot(self.data['ExC'], self.data['Mec'], label=r'$\sigma\tau$ + 2bc')
    plt.xlabel(r'$E_x$')
    plt.ylabel(r'$M^{2\nu}$')
    line=[]
    exp = 0.03846
    for x in range(len(self.data['ExC'])):
      line.append(exp)
    plt.plot(self.data['ExC'], line, label=f'EXP = {exp}')
    plt.legend()
    fig.savefig(f'{self.outdir}/{self.name}.png')

