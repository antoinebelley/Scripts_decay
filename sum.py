## This script will automatically sum up nutbar results into an M2nu NME
## The nutbar results come from properly executing nuM2nu.py (so do this first)
## In particular, we calculate the decay: (ZI,A) -> (ZK,A) + e + v [fictituous intermediate state] -> (ZF,A) + 2e + 2v, where ZI=Z, ZK=Z+1, and ZF=Z+2
## With: initial (I) -> intermediate (K) -> final (F)
## NOTE: you must add in the relevant $Eshift and $EXP to 'the $Eshift/$EXP if-else ladder' below
## all output files are saved in $nucI/$mydir/$outdir, as set below
##  By: Antoine Belley
##  Copyright (C): 2019

import argparse
import sys
import re
import os
import glob
import shutil


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
from make_plot import *
from M2nu_class import *

#Parse the argument to execute the file
parser = argparse.ArgumentParser()
parser.add_argument('ZI',     help = 'Atomic (proton) number of the initial nucleus (I)', type=int)
parser.add_argument('A',      help = 'Mass number of the decay', type=int)
parser.add_argument('emax',   help = 'Value of the maximal energy of the valence space', type=int)
parser.add_argument('hw',     help = 'Value of the frequency of the oscillatory basis', type =int)
parser.add_argument('neigK',  help = 'The number of eigenstates to create for summing over the K excitation energies.', type=int)
args = parser.parse_args()


#Initiate the intances of data_M2nu for each shift and correction option
data_mine_abin = data_M2nu(args.ZI, args.A, args.emax, args.hw, args.neigK, 'mine', 'off')
data_mine_corr = data_M2nu(args.ZI, args.A, args.emax, args.hw, args.neigK, 'mine', 'on')
data_lit_abin  = data_M2nu(args.ZI, args.A, args.emax, args.hw, args.neigK, 'lit', 'off')
data_lit_corr  = data_M2nu(args.ZI, args.A, args.emax, args.hw, args.neigK, 'lit', 'on')

#Create the directory that will hold the results for the isotope
os.makedirs(f'{data_lit_abin.nucI}/results', exist_ok = True)
outdir = f'{data_lit_abin.nucI}/results/emax{args.emax}_hw{args.hw}'
if os.path.exists(f'{outdir}'):
    shutil.rmtree(f'{outdir}')
os.makedirs(f'{outdir}')

#Print checks before running the sum
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print(f'A           =  {args.A}')
print(f'nucI        =  {data_mine_abin.nucI}')
print(f'nucK        =  {data_mine_abin.nucK}')
print(f'nucF        =  {data_mine_abin.nucF}')
print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print(f'neigK       =  {args.neigK}')
print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print(f'SigmaTauDir =  {data_mine_abin.SigmaTauDir}')
print(f'SrgDir      =  {data_mine_abin.SrgDir}')
print(f'MecDir      =  {data_mine_abin.MecDir}')
print(f'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

incheck = input('Is this input acceptable: ')
print('')
if incheck == 'n' or incheck == 'N':
  print('Exiting ...')
  exit(1)


#Calculate the NMEs and save them in dat file to be plotted
data_mine_abin.write_plot_file()
data_mine_corr.write_plot_file()
data_lit_abin.write_plot_file()
data_lit_corr.write_plot_file()


#Write the output files containing the final results
data_mine_abin.write_output_file()
data_mine_corr.write_output_file()
data_lit_abin.write_output_file()
data_lit_corr.write_output_file()


# Write a file containing the cummulative info for all the shifts/corrections
# Also write the tupples to be added to ResultsTable.py
f = open(f'{outdir}/final_results.txt', 'w')
for data in [data_mine_abin, data_mine_corr, data_lit_abin, data_lit_corr]:
  f.write(f'For shift = {data.shift} and correction = {data.correction}:\n\t')
  f.write(f'M2nu           = {data.M2nu_result}\n\t')
  f.write(f'M2nu*0.82*0.82 = {data.M2nuQ82_result}\n\t')
  f.write(f'M2nu*0.77*0.77 = {data.M2nuQ77_result}\n\t')
  f.write(f'M2nu*0.74*0.74 = {data.M2nuQ74_result}\n\t')
  f.write(f'M2nu(SRG)      = {data.M2nuSrg_result}\n\t')
  f.write(f'M2nu(SRG+MEC)  = {data.M2nuMec_result}\n')
  f.write('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')
for data in [data_mine_abin, data_mine_corr, data_lit_abin, data_lit_corr]:
  f.write(f'{data.name} = ({data.M2nu_result}, {data.M2nuQ82_result}, {data.M2nuQ77_result}, {data.M2nuQ74_result}, {data.M2nuSrg_result}, {data.M2nuMec_result})\n')
f.close()

#Print the output

for data in [data_mine_abin, data_mine_corr, data_lit_abin, data_lit_corr]:
  print(f'For shift = {data.shift} and correction = {data.correction}:')
  print(f'\tM2nu           = {data.M2nu_result}')
  print(f'\tM2nu*0.82*0.82 = {data.M2nuQ82_result}')
  print(f'\tM2nu*0.77*0.77 = {data.M2nuQ77_result}')
  print(f'\tM2nu*0.74*0.74 = {data.M2nuQ74_result}')
  print(f'\tM2nu(SRG)      = {data.M2nuSrg_result}')
  print(f'\tM2nu(SRG+MEC)  = {data.M2nuMec_result}')
  print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')


data_mine_abin.make_plot()
data_mine_corr.make_plot()
data_lit_abin.make_plot()
data_lit_corr.make_plot()





  
