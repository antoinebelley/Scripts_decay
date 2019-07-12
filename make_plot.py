import os

if str(os.environ['HOSTNAME']) == 'oak.arc.ubc.ca':
    imasms = '/global/home/belley/Scripts_decay/'                           # " " " " " " nuqsub.py script lives
elif str(os.environ['HOSTNAME'])[7:] == 'cedar.computecanada.ca':
    imasms = '/home/belleya/projects/def-holt/belleya/Scripts_decay/'       # " " " " " " nuqsub.py script lives
else:
    print('This cluster is not known')
    print('Add the paths to execute_M2nu.py in this cluster')
    print('Exiting...')
    exit(1)


import sys
sys.path.insert(0, 'imasms')
from plot import easy_plot


def make_plot(nucI, chift, abinopt, mydir, mydir_MEC, qf, outdir,emax):
    pwd = os.getcwd()
    fileuq      = pwd+'/'+nucI+'/'+mydir+'/'+outdir+'/unquenched_partialssums.dat'
    fileq       = pwd+'/'+nucI+'/'+mydir+'/'+outdir+'/quenched_partialssums.dat'
    fileMEC     = pwd+'/'+nucI+'/'+mydir_MEC+'/'+outdir+'/unquenched_partialssums.dat'
    outfigure   = emax+'_'+chift+'_'+abinopt
    outpath     = '/home/belleya/scratch/belleya/M2nu/plots'

    figure = easy_plot(outfigure, title = 'VS-IMSRG 1.8/2.0 (EM)', 
                                    xlabel = r"$E_x$", ylabel = r'$M^{2\nu}$',
                                    legends = ["Unquenched", "q = "+str(qf), "Value with MEC"],
                                    files   = [fileuq, fileq, fileMEC])
    figure.plot('all', path = outpath, line=0.03846)
    os.sys('rm *png')
    