####################################################################################
#
#                                   README
#                               SGE MODULE 
#
#       This module is designed for sending jobs to the HPC clustal !
#
#       Resources:
#               *
#       Structure:
#              class sungrid
#                      def __init__
#                      def send_jobs
#               
#
####################################################################################

import paramiko, uuid, os, logging, sys,random
from hpc.motivation import uwu_quotes
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logging.info(random.choice(uwu_quotes))

class Slurm():
    """Send jobs to HPC cluster through SGE queueing system !
    """

    def __init__(self, **kwargs):
        """Initialize the SGE object.Connect to Server using `paramiko`
        Structure:
            1. Define variables
            2. Connect to HPC sge
        """
        # 1. Define variables
        self.host = kwargs.get("host", 'irblogin01.irbbarcelona.pcb.ub.es')
        self.username = kwargs.get("username", 'ddalton')
        self.password = kwargs.get("password", '')
        
        # 2. Connect to HPC sge
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.username, password=self.password)
        except paramiko.SSHException as sshException:
            raise Exception(
                "Unable to establish SSH connection: %s" % sshException)
        finally:
            ssh.close()

    def submit_job( 
                    self,
                    script_py,
                    time,
                    mem,
                    cpus,
                    array=1-1,
                    ntasks=1,
                    N=None,
                    args=None,
                    sh_path=None,
                    eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                    image="/home/sbnb/ddalton/singularity_images/cc_py37.simg",
                    cc_image=True,
                    os_remove=True,
                    partition=None,
                    exclude = None
                    ):
        job_script = """\
#!/bin/bash
%(options)s

# Loads default environment configuration

ml load Singularity
# source singularity
#source /apps/manual/software/Singularity/3.9.6/etc/profile
# for DB servers connection
# CUDA drivers
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"
%(commands)s
"""

        if N is None:
            N = script_py.split(".py")[0] 
        if args is None:
            args = len(script_py.split(" ")) # nº of arguments
            args_str = ["$%d" %i for i in range(1,args+1)]
            args_str = " ".join(args_str)
            logging.debug(args)
        if sh_path is None:
            sh_path = str(os.getcwd())
            
        options= """
#SBATCH --job-name=%(N)s
#SBATCH --time=%(time)s          # adjust this to match the walltime of your job
#SBATCH --cpus-per-task=%(cpus)d      # adjust this if you are using parallel commands
#SBATCH --mem=%(mem)dGB              # adjust this according to the memory requirement per node you need
#SBATCH --output=%(eo_path)s%(N)s.%%j.out
# End of qsub options"""%({"N":N,"time":time,"cpus":cpus,"mem":mem,"eo_path":eo_path})
        
        if partition:
            options = options + "\n#SBATCH --partition %s" %(partition)
        if exclude:
            options = options + "\n#SBATCH --exclude=%s" %(exclude)

        # Define commands
        if cc_image: # if we use chemicalchecker or not!
            commands = "/apps/easybuild/common/software/Singularity/3.11.3/bin/singularity exec %(image)s python %(args)s" %({"image":image,"args":args_str})      
        else:
            commands = "/apps/easybuild/common/software/Singularity/3.11.3/bin/singularity exec %(image)s python %(args)s" %({"image":image,"args":args_str})  
        logging.debug(job_script%({"options":options,"commands":commands}))


        # 2. Write jobscript.sh file
        jobname_sh = "job_%s.sh"%str(uuid.uuid4())[:4]
        jobname_sh_path = os.path.join(sh_path, jobname_sh)
        
        f = open(jobname_sh_path,"w")
        f.write(job_script%({"options":options,"commands":commands}))
        f.close()

        # 3. Send Job to HPC sge
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.username, password=self.password)
            
            _stdin, _stdout,_stderr = ssh.exec_command("cd %(sh_path)s;sbatch %(job_sh)s %(script_py)s"
                                            %({ "sh_path":sh_path.replace("/aloy/home/","/home/sbnb/"),
                                                "job_sh":jobname_sh,
                                                "script_py":script_py}))
            print("cd %(sh_path)s;sbatch %(job_sh)s %(script_py)s"
                                            %({ "sh_path":sh_path.replace("/aloy/home/","/home/sbnb/"),
                                                "job_sh":jobname_sh,
                                                "script_py":script_py}))
            logging.debug(_stdout.read().decode())
            logging.debug(_stderr.read().decode())
            
        except paramiko.SSHException as sshException:
            raise Exception(
                "Unable to establish SSH connection: %s" % sshException)
        finally:
            ssh.close()
            if os_remove is True:
                os.remove(jobname_sh)
