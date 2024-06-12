import os
import uuid
import random
import logging
import paramiko
from .motivation import shreck_quotes

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logging.info(random.choice(shreck_quotes))

class Slurm:
    """Send jobs to HPC cluster through SLURM queueing system."""

    def __init__(self, **kwargs):
        """
        Initialize the SLURM object and connect to the server using paramiko.

        Args:
            host (str): The hostname of the server. Default is 'irblogin01.irbbarcelona.pcb.ub.es'.
            username (str): The username for SSH. Default is 'ddalton'.
            password (str): The password for SSH.
        """
        self.host = kwargs.get("host", 'irblogin01.irbbarcelona.pcb.ub.es')
        self.username = kwargs.get("username", 'ddalton')
        self.password = kwargs.get("password", '')

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)
            logging.debug("Successful connection to %s", self.host)
        except paramiko.SSHException as e:
            logging.error("Unable to establish SSH connection: %s", e)
            raise e

    def submit_job(self, script_py, time, mem, cpus, array="1-1", ntasks=1, N=None, args=None,
                   sh_path=None, eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   image="/home/sbnb/ddalton/singularity_images/cc_py37.simg",
                   cc_image=True, os_remove=True, partition=None, exclude=None):
        """
        Submit a job to the SLURM queue.

        Args:
            script_py (str): Path to the Python script to run.
            time (str): The time for the job in format HH:MM:SS.
            mem (int): The memory requirement in GB.
            cpus (int): Number of CPUs required.
            array (str): Job array specification. Default is "1-1".
            ntasks (int): Number of tasks.
            N (str): Job name. Defaults to the script name if not provided.
            args (str): Arguments for the script.
            sh_path (str): Path to write the job script. Defaults to current directory.
            eo_path (str): Path for standard output and error files.
            image (str): Path to the Singularity image.
            cc_image (bool): Use chemicalchecker environment.
            os_remove (bool): Remove the job script after submission.
            partition (str): Partition to submit the job to.
            exclude (str): Nodes to exclude.
        """
        if N is None:
            N = os.path.splitext(os.path.basename(script_py))[0]

        if args is None:
            args_str = " ".join(f"${i}" for i in range(1, len(script_py.split(" ")) + 1))
        else:
            args_str = args

        if sh_path is None:
            sh_path = os.getcwd()

        options = f"""
#SBATCH --job-name={N}
#SBATCH --time={time}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}GB
#SBATCH --output={eo_path}/{N}.%j.out
"""

        if partition:
            options += f"\n#SBATCH --partition={partition}"
        if exclude:
            options += f"\n#SBATCH --exclude={exclude}"

        commands = f"singularity exec {image} python {args_str}"

        job_script = f"""#!/bin/bash
{options}

ml load Singularity
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"
{commands}
"""

        jobname_sh = f"job_{uuid.uuid4().hex[:4]}.sh"
        jobname_sh_path = os.path.join(sh_path, jobname_sh)

        with open(jobname_sh_path, "w") as f:
            f.write(job_script)

        try:
            _stdin, _stdout, _stderr = self.ssh.exec_command(f"cd {sh_path}; sbatch {jobname_sh} {script_py}")
            logging.debug(_stdout.read().decode())
            logging.debug(_stderr.read().decode())
        except paramiko.SSHException as e:
            logging.error("Unable to establish SSH connection: %s", e)
            raise e
        finally:
            self.ssh.close()
            if os_remove:
                os.remove(jobname_sh_path)
