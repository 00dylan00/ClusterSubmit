import os
import uuid
import random
import logging
import paramiko
from .motivation import shreck_quotes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')
logging.info(random.choice(shreck_quotes))

class Sungrid:
    """Send jobs to HPC cluster through SGE queueing system."""

    def __init__(self, **kwargs):
        """
        Initialize the Sungrid object and connect to the server using paramiko.

        Args:
            host (str): The hostname of the server. Default is 'pac-one-head'.
            username (str): The username for SSH. Default is 'ddalton'.
            password (str): The password for SSH.
        """
        self.host = kwargs.get("host", 'pac-one-head')
        self.username = kwargs.get("username", 'ddalton')
        self.password = kwargs.get("password", '')

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)
            logging.debug("Successfully connected to %s", self.host)
        except paramiko.SSHException as e:
            logging.error("Unable to establish SSH connection: %s", e)
            raise e

    def submit_job(self, script_py, pe, mem_free_tot=2, h_vmem_tot=2.2, N=None, os_remove=True,
                   sh_path=None, q=None, wd=None, eo="/aloy/home/ddalton/area_52/scripts/run_log",
                   image="/aloy/home/ddalton/cc/artifacts/images/cc_py37.simg", cc_image=False, args=None):
        """
        Submit a job to the SGE queue.

        Args:
            script_py (str): Path to the Python script to run.
            pe (int): Number of cores/slots requested.
            mem_free_tot (int): Total memory requested in GB.
            h_vmem_tot (int): Total virtual memory limit in GB.
            N (str): Job name. Defaults to the script name if not provided.
            os_remove (bool): Remove the job script after submission.
            sh_path (str): Path to write the job script. Defaults to the current directory.
            q (str): Requested queue.
            wd (str): Working directory.
            eo (str): Directory for std.err and std.output.
            image (str): Path to the Singularity image.
            cc_image (bool): Use chemicalchecker environment.
            args (str): Arguments for the script.
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
#$ -S /bin/bash
#$ -N {N}
#$ -e {eo}
#$ -o {eo}
#$ -pe make {pe}
#$ -r yes
#$ -j yes
#$ -l mem_free={mem_free_tot}.0G,h_vmem={h_vmem_tot}.0G
"""

        if q:
            options += f"\n#$ -q {q}"
        if wd:
            options += f"\n#$ -wd {wd}"
        else:
            options += "\n#$ -cwd"

        commands = f"""
OMP_NUM_THREADS={pe} OPENBLAS_NUM_THREADS={pe} MKL_NUM_THREADS={pe} VECLIB_MAXIMUM_THREADS={pe} NUMEXPR_NUM_THREADS={pe} NUMEXPR_MAX_THREADS={pe} singularity exec {image} python {args_str}
"""

        job_script = f"""#!/bin/bash
{options}

# Loads default environment configuration 
if [[ -f $HOME/.bashrc ]]; then
  source $HOME/.bashrc
fi
{commands}
"""

        jobname_sh = f"job_{uuid.uuid4().hex[:4]}.sh"
        jobname_sh_path = os.path.join(sh_path, jobname_sh)

        with open(jobname_sh_path, "w") as f:
            f.write(job_script)

        try:
            _stdin, _stdout, _stderr = self.ssh.exec_command(f"cd {sh_path}; qsub {jobname_sh} {script_py}")
            logging.debug(_stdout.read().decode())
            logging.debug(_stderr.read().decode())
        except paramiko.SSHException as e:
            logging.error("Unable to establish SSH connection: %s", e)
            raise e
        finally:
            self.ssh.close()
            if os_remove:
                os.remove(jobname_sh_path)
