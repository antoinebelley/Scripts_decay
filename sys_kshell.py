#!/usr/bin/env python
import os
import sys
import subprocess
HOME=os.path.expanduser("~")
sys.path.append(HOME)
#from mylib_python import plotlevel
path_to_kshell=HOME+"/projects/def-holt/shared/KSHELL/version-2019-08-15/"


n_nodes=10
n_threads=32
time = "0-06:00"
mem = "4000M"
account="rrg-holt"

#valence_space = 'sd'
core = (50,50)
valence_space = 'sdg7h11'
core = (28,28)
valence_space = 'pf5g9'
#core = (8,20)
#valence_space = 'proton_sd_neutron_f7p3'
#states = "0+5,2+5"


def reset_header(f_sh, account, n_nodes, n_threads, time, mem):
    header = "#!/bin/bash\n"
    # header += "#SBATCH --account="+account+"\n"
    # header += "#SBATCH --nodes="+str(n_nodes)+"\n"
    # header += "#SBATCH --ntasks-per-node=1\n"
    # header += "#SBATCH --cpus-per-task="+str(n_threads)+"\n"
    # header += "#SBATCH --mem-per-cpu="+mem+"\n"
    # header += "#SBATCH --time="+time+"\n\n"
    f = open(f_sh, "r")
    lines = f.readlines()
    f.close()
    line_num = 0
    for line in lines:
        if(line.find("echo") != -1): break
        line_num += 1
    sh = header
    for line in lines[line_num:]:
        sh += line
    f = open(f_sh, "w")
    f.write(sh)
    f.close()


#interaction = "N4LO_3Nlnl"
#interaction = "magic_3N_EM1.8_2.0"
def write_job_kshell(Z,A,name):
    # ELEM        = ['blank', 'h', 'he',
    #                'li', 'be', 'b',  'c',  'n',  'o', 'f',  'ne',
    #                'na', 'mg', 'al', 'si', 'p',  's', 'cl', 'ar',
    #                'k',  'ca', 'sc', 'ti', 'v',  'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br', 'kr',
    #                'rb', 'sr', 'y',  'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te', 'i',  'xe',
    #                'cs', 'ba', 'la', 'ce', 'pr', 'nd', 'pm', 'sm'] # an array of elements from Hydrogen (Z=1) to Samarium (Z=62), includes all current 0vbb candidates
    core = (28,28)
    valence_space = 'pf5g9'
    states = "+1"
    for Z in [Z,Z+2]:
        N = A - Z
        for e in [8]:
            valence_z = Z - core[0]
            valence_n = N - core[1]
            if(valence_z < 0 or valence_n < 0): continue
            #nucl = ELEM[Z]
            snt = name
            f_sh = name # no truncation
            if(not os.path.isfile(snt)):
                print(snt, "not found")
                continue
            f = open('ui.in','w')
            f.write('cedar1\n')
            f.write(snt+'\n')
            f.write(str(valence_z)+","+str(valence_n)+'\n')
            f.write(f_sh+'\n')
            f.write(states+'\n')
            f.write('\n')  # no truncation
            f.write('\n')  # no truncation
            f.write('beta_cm=0\n')
            f.write('\n')
            f.write('\n')
            f.write('\n')
            f.close()
            cmd = 'python2 '+path_to_kshell+'kshell_ui.py < ui.in'
            subprocess.call(cmd, shell=True)
            subprocess.call("rm ui.in", shell=True)
            f_sh += ".sh"
            reset_header(f_sh,account,n_nodes,n_threads,time,mem)
            cmd = "sbatch " + f_sh
                #subprocess.call(cmd, shell=True)
