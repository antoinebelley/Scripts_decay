import pandas as pd
import sys
import os
import glob
import numpy as np
import weakref
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


class Directory():
  """Class containing the function to sum the NME on a particular directory"""
  instances = []

  def __init__(self, nucI, nucK, nucF, BB, inter, emax, hw, neigK, shift, correction, MEC = False, IF = False):
    self.nucI       = nucI
    self.nucK       = nucK
    self.BB         = BB
    self.emax       = emax
    self.hw         = hw
    self.neigK      = neigK
    self.correction = correction
    self.MEC        = MEC
    self.IF         = IF
    #Find the path (and make sure that it exists) to the directory
    if BB != 'OS':
      directory = f'{nucI}/M2nu*_{BB}_*{inter}*e{emax}*hw{hw}*neig{neigK}'
    else:
      directory = f'{nucI}/M2nu*_{BB}_*e{emax}*hw{hw}*neig{neigK}'
    if MEC == True:
      directory = f'{directory}_MEC'
    if IF == True and MEC != True:
      directory = f'{directory}_IF'
    try:
      directory = glob.glob(f'{directory}')[0]
    except IndexError:
      print(f'ERROR: Cannot find {directory}')
      print('Exiting...')
      exit(1)
    self.path = glob.glob(f'{directory}')[0]
    #Make sure those are the same then in goM2nu.py
    self.directory = directory
    self.KIdir    = 'KI_nutbar'
    self.FKdir    = 'FK_nutbar'
    self.nudirI   = 'nushxI_data'
    self.nudirKgs = 'gs_nushxK_data'
    self.nudirK   = 'nushxK_data'
    self.nudirF   = 'nushxF_data'
    self.nutfileK  = f'nutbar_tensor1_{nucK}0_{nucI}0.dat'
    self.nutfileF  = f'nutbar_tensor1_{nucF}0_{nucK}0.dat'
    #Verify that the nutbar file exists and have the same number of lines
    verify_nutbar(nucK, nucF, directory, self.KIdir, self.FKdir, self.nutfileK, self.nutfileF)
    #Go get the experimental value of the energie shift and the ExP enrgy of the ground state
    self.EXP, self.Eshift = getEXP(shift, nucK)
    #Create list of the instances of the class
    self.__class__.instances.append(weakref.proxy(self))

  def sumNME(self):
    """Calculate the M2nu for the OS op with the gx1apn interaction"""
    EKgs = read_Egs(f'{self.nucK}', f'{self.path}/{self.nudirKgs}')
    M2nu    = 0 # initialize the sum over K
    Cexp    = 0 # initialize the correction value = $EXP - min($EK-$EKgs)
    maxKsum = self.neigK+8
    M2nu_array  = []
    ExC_array   = []
    factor         = -3.419935
    if self.MEC == False and self.IF == False:
      for i in range(7,maxKsum-1):
        EK, nmeKI = read_Eses(state = i, directory = f'{self.path}/{self.KIdir}', file = self.nutfileK)
        EF, nmeFK = read_Eses(state = i, directory = f'{self.path}/{self.FKdir}', file = self.nutfileF)
        Ex        = EK-EKgs                           # the excitation energy     
        if self.correction == 'corr' and i == 7:
            Cexp = self.EXP - Ex                         # the experimental energy correction value
        ExC   = Ex+Cexp
        denom = ExC+self.Eshift                    # denominator of the sum
        M2nu  = single_M2nu(nmeKI, nmeFK, M2nu ,denom)
        aM2nu = abs(M2nu)
        M2nu_array.append(aM2nu)
        ExC_array.append(ExC)
      M2nu_array = np.array(M2nu_array)
      ExC_array  = np.array(ExC_array)
      self.ExC   = ExC_array
      return M2nu_array
    elif self.MEC == True:
      directory = f'{self.nucI}/M2nu*_{self.BB}_*e{self.emax}*hw{self.hw}*neig{self.neigK}'
      path = glob.glob(f'{directory}')[0]
      for i in range(7,maxKsum-1):
        EK, nmeKI = read_Eses(state = i, directory = f'{path}/{self.KIdir}', file = self.nutfileK)
        EF, nmeFK = read_Eses(state = i, directory = f'{path}/{self.FKdir}', file = self.nutfileF)
        Ex        = EK-EKgs                           # the excitation energy     
        if self.correction == 'corr' and i == 7:
            Cexp = self.EXP - Ex                         # the experimental energy correction value
        ExC   = Ex+Cexp
        denom = ExC+self.Eshift                    # denominator of the sum
        #Calculate for MEC where nmeKI = nmeKISRG - factor nmeKIMEC and similarly for nmeFK
        EK_MEC, nmeKI_MEC = read_Eses(state = i, directory = f'{self.path}/{self.KIdir}', file = self.nutfileK)
        EF_MEC, nmeFK_MEC = read_Eses(state = i, directory = f'{self.path}/{self.FKdir}', file = self.nutfileF)
        nmeKI_MEC *= factor
        nmeFK_MEC *= factor
        nmeKI_MEC = nmeKI + nmeKI_MEC
        nmeFK_MEC = nmeFK + nmeFK_MEC
        M2nu  = single_M2nu(nmeKI_MEC, nmeFK_MEC, M2nu ,denom)
        aM2nu = abs(M2nu)
        M2nu_array.append(aM2nu)
        ExC_array.append(ExC)
      M2nu_array = np.array(M2nu_array)
      ExC_array  = np.array(ExC_array)
      self.ExC   = ExC_array
      return M2nu_array
    elif self.IF == True:
      directory = f'{self.nucI}/M2nu*_{self.BB}_*e{self.emax}*hw{self.hw}*neig{self.neigK}'
      path      = glob.glob(f'{directory}')[0]
      dirMEC    = f'{directory}_MEC'
      path_MEC  =glob.glob(f'{dirMEC}')[0]
      for i in range(7,maxKsum-1):
        EK, nmeKI = read_Eses(state = i, directory = f'{path}/{self.KIdir}', file = self.nutfileK)
        EF, nmeFK = read_Eses(state = i, directory = f'{path}/{self.FKdir}', file = self.nutfileF)
        Ex        = EK-EKgs                           # the excitation energy     
        if self.correction == 'corr' and i == 7:
            Cexp = self.EXP - Ex                         # the experimental energy correction value
        ExC   = Ex+Cexp
        denom = ExC+self.Eshift                    # denominator of the sum
        #Calculate NMEs for MEC where nmeKI = nmeKISRG + factor nmeKIMEC and similarly for nmeFK
        EK_MEC, nmeKI_MEC = read_Eses(state = i, directory = f'{path_MEC}/{self.KIdir}', file = self.nutfileK)
        EF_MEC, nmeFK_MEC = read_Eses(state = i, directory = f'{path_MEC}/{self.FKdir}', file = self.nutfileF)
        nmeKI_MEC *= factor
        nmeFK_MEC *= factor
        nmeKI_MEC = nmeKI + nmeKI_MEC
        nmeFK_MEC = nmeFK + nmeFK_MEC
        #Calculate NMES for IF where nmeKI = nmeKISRG + factor*nmeKIMEC + factor*nmeIF and similarly for nmeFK
        EK_IF, nmeKI_IF = read_Eses(state = i, directory = f'{self.path}/{self.KIdir}', file = self.nutfileK)
        EF_IF, nmeFK_IF = read_Eses(state = i, directory = f'{self.path}/{self.FKdir}', file = self.nutfileF)
        nmeKI_IF *= factor
        nmeFK_IF *= factor
        nmeKI_IF = nmeKI_MEC + nmeKI_IF
        nmeFK_IF = nmeFK_MEC + nmeFK_IF
        M2nu  = single_M2nu(nmeKI_IF, nmeFK_IF, M2nu ,denom)
        aM2nu = abs(M2nu)
        M2nu_array.append(aM2nu)
        ExC_array.append(ExC)
      M2nu_array = np.array(M2nu_array)
      ExC_array  = np.array(ExC_array)
      self.ExC     = ExC_array
      return M2nu_array


class DataM2nu():
  """Creates data frame and output file for all the directory necessary"""
  def __init__(self, Z, A, inter, emax, hw, neigK, shift, correction):
    self.ZI          = Z
    self.A           = A
    self.emax        = emax
    self.hw          = hw
    self.name        = f'{shift}_{correction}'
    self.inter       = inter
    self.shift       = shift
    self.correction  = correction
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
    #Create instances of the directories
    self.Gx1apnDir   = Directory(self.nucI, self.nucK, self.nucF, 'OS', inter, emax, hw, neigK, shift, correction)
    self.SigmaTauDir = Directory(self.nucI, self.nucK, self.nucF, 'HF', inter, emax, hw, neigK, shift, correction)
    self.SrgDir      = Directory(self.nucI, self.nucK, self.nucF, '3N', inter, emax, hw, neigK, shift, correction)
    self.MecDir      = Directory(self.nucI, self.nucK, self.nucF, '3N', inter, emax, hw, neigK, shift, correction, MEC = True)
    if inter == 'N4LO':
      self.IfDir     = Directory(self.nucI, self.nucK, self.nucF, '3N', inter, emax, hw, neigK, shift, correction, IF = True)
    #Directrory where to write the results
    self.outdir = f'{self.nucI}/results/{inter}_emax{emax}_hw{hw}'
    #Go get the experimental value of the energie shift and the ExP enrgy of the ground state
    self.EXP, self.Eshift = getEXP(shift, self.nucK)


  def sumNMESall(self):
    """Sum all the NMEs, remark that for the Mec and If, 
    we need to add them to them to the Srg resukt and need to
    multiple by another factor. This comes from Peter's files for
    the interractions"""
    
    self.M2nu      = self.Gx1apnDir.sumNME()
    self.ExC       = self.Gx1apnDir.ExC
    self.M2nuQ82   = self.M2nu*0.82*0.82
    self.M2nuQ77   = self.M2nu*0.77*0.77
    self.M2nuQ74   = self.M2nu*0.74*0.74
    self.M2nuSig   = self.SigmaTauDir.sumNME()
    self.M2nuSrg   = self.SrgDir.sumNME()
    self.M2nuMec   = self.MecDir.sumNME()
    if self.inter == 'N4LO':
      self.M2nuIF  = self.IfDir.sumNME()

  def getdataframe(self):
    """Creates a pandas dataframe with the data to make it easier to plot the result"""
    if self.inter == 'N4LO':
      columns = ['ExC', 'Gx1apn','qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec', 'Mec+IF']
      try :
        data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.M2nuSig, self.M2nuSrg, self.M2nuMec, self.M2nuIF])
      except AttributeError:
        self.sumNMESall()
        data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.M2nuSig, self.M2nuSrg, self.M2nuMec, self.M2nuIF])
    else:
      columns = ['ExC', 'Gx1apn','qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec']
      try :
        data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.M2nuSig, self.M2nuSrg, self.M2nuMec])
      except AttributeError:
        self.sumNMESall()
        data = np.array([self.ExC, self.M2nu, self.M2nuQ82, self.M2nuQ77, self.M2nuQ74, self.M2nuSig, self.M2nuSrg, self.M2nuMec])
    data = pd.DataFrame(data.transpose())
    data.columns = columns
    self.data = data

  def write_plot_file(self):
    plotfile = f'plot_{self.name}.dat'
    if self.inter == 'N4LO':
      try:
        self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                        'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec', 'Mec+IF'], index=False)
      except:
        self.getdataframe()
        self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                        'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec', 'Mec+IF'], index=False)
    if self.inter == 'N4LO':
      try:
        self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                        'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec'], index=False)
      except:
        self.getdataframe()
        self.data.to_csv(f'{self.outdir}/{plotfile}',sep = '\t', header =['ExC', 'Gx1apn', 
                        'qf = 0.82', 'qf = 0.77', 'qf = 0.74', 'SigmaTau', 'Srg', 'Mec'], index=False)
  
  def write_output_file(self):
    outfile = f'results_{self.name}.txt'

    f = open(f'{self.outdir}/{outfile}', 'w')
    f.write(f'Shift         =  {self.shift}\n')
    f.write(f'Correction    =  {self.correction}\n')
    f.write(f'nucI          =  {self.nucI}\n')
    f.write(f'nucK          =  {self.nucK}\n')
    f.write(f'nucF          =  {self.nucF}\n')
    f.write(f'Eshift        =  {self.Eshift}\n')
    f.write(f'EXP           =  {self.EXP}\n\n')
    M2nu      = self.M2nu[len(self.M2nu)-1]
    M2nuQ82   = self.M2nuQ82[len(self.M2nu)-1]
    M2nuQ77   = self.M2nuQ77[len(self.M2nu)-1]
    M2nuQ74   = self.M2nuQ74[len(self.M2nu)-1]
    M2nuSig   = self.M2nuSig[len(self.M2nu)-1]
    M2nuSrg   = self.M2nuSrg[len(self.M2nu)-1]
    M2nuMec   = self.M2nuMec[len(self.M2nu)-1]
    if self.inter == 'N4LO':
      M2nuIf    = self.M2nuIf[len(self.M2nu)-1]
    f.write('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    f.write('... and the caclulations come to!\n\n')
    f.write(f'M2nu                 = {M2nu}\n')
    f.write(f'M2nu*0.82*0.82       = {M2nuQ82}\n')
    f.write(f'M2nu*0.77*0.77       = {M2nuQ77}\n')
    f.write(f'M2nu*0.74*0.74       = {M2nuQ74}\n')
    f.write(f'M2nu(sigtau)         = {M2nu}\n')
    f.write(f'M2nu(SRG)            = {M2nuSrg}\n')
    f.write(f'M2nu(SRG+MEC)        = {M2nuMec}\n')
    if self.inter == 'N4LO':
      f.write(f'M2nu(SRG+MEC+IF)     = {M2nuIf}\n')
    f.close()
    self.M2nu_result      = M2nu
    self.M2nuQ82_result   = M2nuQ82
    self.M2nuQ77_result   = M2nuQ77
    self.M2nuQ74_result   = M2nuQ74
    self.M2nuSig_result   = M2nuSig
    self.M2nuSrg_result   = M2nuSrg
    self.M2nuMec_result   = M2nuMec
    if self.inter == 'N4LO':
      self.M2nuIf_result    = M2nuIf

  def make_plot(self):
    fig = plt.figure()
    plt.plot(self.data['ExC'], self.data['Gx1apn'], label='gx1apn')
    plt.plot(self.data['ExC'], self.data['qf = 0.82'], label='qf=0.82')
    plt.plot(self.data['ExC'], self.data['SigmaTau'], label=r'$\sigma\tau$')
    plt.plot(self.data['ExC'], self.data['Srg'], label=r'$\sigma\tau$(srg)')
    plt.plot(self.data['ExC'], self.data['Mec'], label=r'$\sigma\tau$ + 2bc')
    if self.inter == 'N4LO':
      plt.plot(self.data['ExC'], self.data['Mec+IF'], label=r'$\sigma\tau$ + 2bc + IF')
    plt.xlabel(r'$E_x$')
    plt.ylabel(r'$M^{2\nu}$')
    line=[]
    exp = 0.03846
    for x in range(len(self.data['ExC'])):
      line.append(exp)
    plt.plot(self.data['ExC'], line, label=f'EXP = {exp}')
    plt.legend()
    fig.savefig(f'{self.outdir}/{self.name}.png')

