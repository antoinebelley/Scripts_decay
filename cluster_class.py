#This a class for the different cluster you can submit to. (Oak/Cedar in my case)
#Allows for easier/further automation when submitting jobs

from subprocess import call,PIPE
import os

class WrongJobScheduler(Exception):
	"Raised when the a cluster is created in the wrong subclass"
	pass
	

class cluster:
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
	def __init__(self, name, host, maxwall, maxppn, maxvmem, maxnth):
		cluster.__init__(self, name, host)
		self.wall   = maxwall
		self.ppn    = maxppn
		self.vmem   = maxvmem
		self.thread = maxnth
		try:
			if self.BATCHYS != 'PBS':
				raise(WrongJobScheduler)
			break
		except WrongJobScheduler:
			print("The cluster is not using PBS as a job scheduler.")
			print("Job scheduler = "+self.BATCHSYS)
			exit(1)



	def submit_job(self, command, runname, email, wall = None, ppn = None, vmem = None, nth = None):
		clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
		#Verify that the given arguments are inside the allowed values for the specifc cluster
		for x in [wall, ppn, vmem, nth]:
			if x == None:
				clamp(x, 1, self.x)
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
	def __init__(self, name, host, maxvmem, maxnth):
		cluster.__init__(self, name, host)
		self.nth  = maxnth
		self.vmem  = maxvmem
		try:
			if self.BATCHYS != 'SLRUM':
				raise(WrongJobScheduler)
			break
		except WrongJobScheduler:
			print("The cluster is not using PBS as a job scheduler.")
			print("Job scheduler = "+self.BATCHSYS)
			exit(1)


	def submit_job(self, command, runname, email, vmem = None, nth = None, time = '24:00:00'):
		clamp = lambda n, minn, maxn,: max(min(maxn,n), minn)
		#verify that the given arguments are inside the allowed values for the specific cluster
		for x in [vmem, nth]:
			if x == None:
				clamp(x, 1, self.x)
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


cedar = SLURM('cedar', 'cedar.computecanada.ca', 250,32)
oak   = PBS('oak', 'oak.arc.ubc.ca', 512, 32, 251, 32)


