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

import paramiko, uuid, os, logging, sys
from hpc.motivation import uwu_quotes
import random


logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logging.info(random.choice(uwu_quotes))

class Sungrid():
    """Send jobs to HPC cluster through SGE queueing system !
    """

    def __init__(self, **kwargs):
        """Initialize the SGE object.Connect to Server using `paramiko`
        Structure:
            1. Define variables
            2. Connect to HPC sge
        """
        # 1. Define variables
        self.host = kwargs.get("host", 'pac-one-head')
        self.username = kwargs.get("username", 'ddalton')
        self.password = kwargs.get("password", '')
        
        # 2. Connect to HPC sge
        try:
            logging.debug("Successful Connection!")
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.username, password=self.password)
        except paramiko.SSHException as sshException:
            raise Exception(
                "Unable to establish SSH connection: %s" % sshException)
        finally:
            ssh.close()

    def submit_job(self,
            script_py,
            pe,
            mem_free_tot = 2,
            h_vmem_tot = 2.2,
            N = None,
            os_remove = True,
            sh_path = None,
            q = None,
            wd = None,
            eo = "/aloy/home/ddalton/area_52/scripts/run_log",
            image = "/aloy/home/ddalton/cc/artifacts/images/cc_py37.simg",
            cc_image = False,
            args = None):
        """Function to send jobs.
            Parameters:
                script_py: string
                    script we will submit (along with any arguments it needs)
                    i.e script_test.py "string" 1234
                pe: int
                    Nº of cores/slots requested
                mem_free_tot: int 
                    total memory requested 
                h_vmem_tot: int
                    Ttal virtual memory limit
                N: string, default=None
                    Job Name - if None it will take script name
                sh_path: string, default=None
                    Path where to run the bash script. If None it will
                    get current working directory
                q: str, default=None
                    Rquested queu i.e.
                wd: string, default=None
                    Working directory
                eo: str, default="/aloy/home/ddalton/area_52/scripts/run_log"
                    Directory for std.err & std.output
                image: str, default="/aloy/home/ddalton/cc/artifacts/images/cc_py37.simg"
                    singularity image
                cc_image: bool, default=False
                    Use or not chemicalchecker environment and config
                args: int, default=None
                    Nº of arguments in bash file i.e python $1 $2 . . . 
            
            Structure:
                1. Define Variables
                2. Write jobscript.sh file
                3. Send Job to HPC sge
        """

        # 1. Define Variables
        job_script = """\
#!/bin/bash
%(options)s

# Loads default environment configuration 
if [[ -f $HOME/.bashrc ]]
then
  source $HOME/.bashrc
fi
%(commands)s
"""
        mem_free = mem_free_tot
        h_vmem   = h_vmem_tot
        if N is None:
            N = script_py.split('/')[0]
            N = N.split(".py")[0] 
        if args is None:
            args = len(script_py.split(" ")) # nº of arguments
            args_str = ["$%d" %i for i in range(1,args+1)]
            args_str = " ".join(args_str)
            logging.debug(args)
        if sh_path is None:
            sh_path = str(os.getcwd())

        # Define Options
        options= """
# Options for qsub 
#$ -S /bin/bash
#$ -N %(N)s
#$ -e %(e)s
#$ -o %(o)s
#$ -pe make %(pe)d
#$ -r yes
#$ -j yes
#$ -l mem_free=%(mem_free).1fG,h_vmem=%(h_vmem).1fG
# End of qsub options"""

        options = options %({"N":N,"e":eo,"o":eo,"pe":pe,"mem_free":mem_free,"h_vmem":h_vmem})

        if q:
            options = options + "\n#$ -q %s" %(q)
        if wd:
            options = options + "\n#$ -wd %s" %(wd)
        else:
            options = options + "\n#$ -cwd"

        # Define commands
        if cc_image: # if we use chemicalchecker or not!
            commands = "OMP_NUM_THREADS=%(pe)s OPENBLAS_NUM_THREADS=%(pe)s MKL_NUM_THREADS=%(pe)s VECLIB_MAXIMUM_THREADS=%(pe)s NUMEXPR_NUM_THREADS=%(pe)s NUMEXPR_MAX_THREADS=%(pe)s SINGULARITYENV_PYTHONPATH=/aloy/home/ddalton/cc_versions/chemical_checker/package/ SINGULARITYENV_CC_CONFIG=/aloy/home/ddalton/cc/config/cc_config_test.json singularity exec %(image)s python %(args)s" %({"pe":pe,"image":image,"args":args_str})  
        else:
            commands = "OMP_NUM_THREADS=%(pe)s OPENBLAS_NUM_THREADS=%(pe)s MKL_NUM_THREADS=%(pe)s VECLIB_MAXIMUM_THREADS=%(pe)s NUMEXPR_NUM_THREADS=%(pe)s NUMEXPR_MAX_THREADS=%(pe)s singularity exec %(image)s python %(args)s" %({"pe":pe,"image":image,"args":args_str})  

        
        logging.debug(job_script%({"options":options,"commands":commands}))
        
        # 2. Write jobscript.sh file
        jobname_sh = "job_%s.sh"%str(uuid.uuid4())[:4]
        jobname_sh_path = os.path.join(sh_path, jobname_sh)
        
        f = open(jobname_sh_path,"w")
        f.write(job_script%({"options":options,"commands":commands}))
        f.close()
        
        #os.chmod(f,0o755)
       
        # 3. Send Job to HPC sge
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.username, password=self.password)
            
            _stdin, _stdout,_stderr = ssh.exec_command("cd %(sh_path)s;qsub %(job_sh)s %(script_py)s"
                                            %({ "sh_path":sh_path,
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