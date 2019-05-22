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
		FILECONTENT = """#!/bin/bash
		#PBS -N %s
		#PBS -q oak
		#PBS -d %s
		#PBS -l walltime=%d:00:00
		#PBS -l nodes=1:ppn=%d
		#PBS -l vmem=%sgb
		#PBS -m ae
		#PBS -M %s
		#PBS -j oe
		#PBS -o %s.pbs.o
		cd $PBS_O_WORKDIR
		export OMP_NUM_THREADS=%d
		%s
		"""
		sfile = open(runname+'.batch','w')
		sfile.write(FILECONTENT%(runname,os.environ['PWD'],wall,ppn,vmem,email,runname,nth,command))
		sfile.close()
		call(['qsub', runname+'.batch'])
		os.remove(runname+'.batch')	
		
		

class SLURM(cluster):
	"Subclass for the clusters using SLURMas job scheduler"
	def __init__(self, name, host, maxvmem, maxnth):
		cluster.__init__(self, name, host)
		self.thread  = maxnth
		self.vmem  = maxvmem


	def submit_job(self, command, runname, email, vmem = None, nth = None, time = '24:00:00'):
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
		FILECONTENT = """#!/bin/bash
		#SBATCH --account=rrg-holt
		#SBATCH --nodes=1
		#SBATCH --ntasks=1
		#SBATCH --cpus-per-task=%d
		#SBATCH --output=NME_log/%s.%%j
		#SBATCH --time=%s
		#SBATCH --mail-user=%s
		#SBATCH --mail-type=END
		#SBATCH --mem=%dG
		cd $SLURM_SUBMIT_DIR
		echo NTHREADS = %d
		export OMP_NUM_THREADS=%d
		time srun %s
		"""
		sfile = open(runname+'.batch','w')
		sfile.write(FILECONTENT%(nth,runname,time,email,nth,nth,command))
		sfile.close()
		call(['sbatch', runname+'.batch'])
		os.remove(runname+'.batch')


#Creates instances for the known cluster
cedar = SLURM('CEDAR', 'cedar.computecanada.ca', 250,32)
oak   = PBS('Oak', 'oak.arc.ubc.ca', 512, 32, 251, 32)


