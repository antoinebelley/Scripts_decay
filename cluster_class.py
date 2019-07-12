#This a class for the different cluster you can submit to. (Oak/Cedar in my case)
#Allows for easier/further automation when submitting jobs

from subprocess import call,PIPE
import os

class WrongJobScheduler(Exception):
	"Raised when the a cluster is created in the wrong subclass"
	pass
	

class cluster:
	"Class to describe the different cluster we can submit job to"
	
	def __init__(self, name, host):
		self.name = name
		self.host = host
		self.BATCHSYS = 'NONE'
		if call('type '+'qsub', shell=True, stdout=PIPE, stderr=PIPE) == 0: self.BATCHSYS = 'PBS'
		elif call('type '+'srun', shell=True, stdout=PIPE, stderr=PIPE) == 0: self.BATCHSYS = 'SLURM'
		

	
	def get_jobsystem(self):
		if self.BATCHSYS == 'NONE':
			print("No job scheduler on "+self.name+".")
		else:
			print(self.name+" uses "+self.BATCHSYS+" as a job scheduler.")


class PBS(cluster):
	"Subclass for the clusters using PBS as job scheduler"
	def __init__(self, name, host, maxwall, maxppn, maxvmem, maxnth):
		cluster.__init__(self, name, host)
		self.wall   = maxwall
		self.ppn    = maxppn
		self.vmem   = maxvmem
		self.thread = maxnth


	def submit_job(self, command, runname, email, wall = None, ppn = None, vmem = None, nth = None):
		clamp = lambda n, minn, maxn: max(min(maxn, n), minn) #Makes sure the value is within a range and set it the boundary if it isn't
		#Verify that the given arguments are inside the allowed values for the specifc cluster
		if wall is None:
			wall = self.wall
		else:
			clamp(wall, 1, self.wall)
		if ppn is None:
			ppn = self.ppn
		else:
			clamp(ppn, 1, self.ppn)
		if vmem is None:
			vmem = self.vmem
		else:
			clamp(vmem, 1, self.vmem)
		if nth is None:
			nth = self.thread
		else:
			clamp(nth, 1, self.thread)
		sfile = open(runname+'.batch','w')
		sfile.write('#!/bin/bash\n')
		sfile.write('#PBS -N '+runname+'\n')
		sfile.write('#PBS -q oak\n')
		sfile.write('#PBS -d '+os.environ['PWD']+'\n')
		sfile.write('#PBS -l walltime='+str(wall)+':00:00\n')
		sfile.write('#PBS -l nodes=1:ppn='+str(ppn)+'\n')
		sfile.write('PBS -l vmem='+str(vmem)+'gb\n')
		sfile.write('#PBS -m ae')
		sfile.write('#PBS -M '+email+'\n')
		sfile.write('#PBS -j oe')
		sfile.write('#PBS -o '+runname+'.pbs.o\n')
		sfile.write('cd $PBS_O_WORKDIR\n')
		sfile.write('export OMP_NUM_THREADS='+str(nth)+'\n')
		sfile.write(command+'\n')
		sfile.close()
		call(['qsub', runname+'.batch'])
		os.remove(runname+'.batch')	
		
		

class SLURM(cluster):
	"Subclass for the clusters using SLURMas job scheduler"
	def __init__(self, name, host, maxvmem, maxnth):
		cluster.__init__(self, name, host)
		self.thread  = maxnth
		self.vmem  = maxvmem


	def submit_job(self, command, runname, logname, email, vmem = None, nth = None, time = '24:00:00'):
		clamp = lambda n, minn, maxn,: max(min(maxn,n), minn) #Makes sure the value is within a range and set it the boundary if it isn't
		#verify that the given arguments are inside the allowed values for the specific cluster
		if vmem is None:
			vmem = self.vmem
		else:
			clamp(vmem, 1, self.vmem)
		if nth is None:
			nth = self.thread
		else: 
			clamp(nth, 1, self.thread)
		sfile = open(runname+'.batch','w')
		sfile.write('#!/bin/bash\n')
		sfile.write('#SBATCH --account=rrg-holt\n')
		sfile.write('#SBATCH --nodes=1\n')
		sfile.write('#SBATCH --ntasks=1\n')
		sfile.write('#SBATCH --cpus-per-task='+str(nth)+'\n')
		sfile.write('#SBATCH --output='+logname+'%j\n')
		sfile.write('#SBATCH --time='+time+'\n')
		sfile.write('#SBATCH --mail-user='+email+'\n')
		sfile.write('#SBATCH --mail-type=END\n')
		sfile.write('#SBATCH --mem='+str(vmem)+'G\n')
		sfile.write('cd $SLURM_SUBMIT_DIR\n')
		sfile.write('echo NTHREADS = '+str(nth)+'\n')
		sfile.write('export OMP_NUM_THREADS='+str(nth)+'\n')
		sfile.write('time srun '+command)
		sfile.close()
		call(['sbatch', runname+'.batch'])
		os.remove(runname+'.batch')


#Creates instances for the known cluster
cedar = SLURM('CEDAR', 'cedar.computecanada.ca', 250,32)
oak   = PBS('Oak', 'oak.arc.ubc.ca', 512, 32, 251, 32)


