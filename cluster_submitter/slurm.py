import paramiko, uuid
import os
import logging
import random
from .motivation import shreck_quotes  # Assume it's an external module

# Set up logging
logging.basicConfig(level=logging.info, format='%(asctime)s :: %(levelname)s :: %(message)s')

class Slurm:
    """Send jobs to HPC cluster through SGE queueing system"""

    def __init__(self, **kwargs):
        """Initialize the SGE object. Connect to Server using paramiko."""
        self.host = kwargs.get("host", 'irblogin01.irbbarcelona.pcb.ub.es')
        self.username = kwargs.get("username", 'ddalton')
        self.password = kwargs.get("password", '')

        self.ssh = None
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise
        finally:
            if self.ssh:
                self.ssh.close()

    def submit_job(self, script_py, time, mem, cpus, array="1-1", ntasks=1, N=None, args=None,
                   sh_path=None, eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   image="/home/sbnb/ddalton/singularity_images/cc_py37.simg", cc_image=True,
                   os_remove=True, partition=None, exclude=None):
        
        """
        Submits a job to an HPC cluster using Slurm.

        Args:
            - script_py (str): The path to the Python script to be executed.
            - time (str): The wall time for the job in the format 'HH:MM:SS'.
            - mem (int): The amount of memory required for the job in GB.
            - cpus (int): The number of CPU cores to allocate for the job.
            - array (str, optional): Defines a job array, by default "1-1".
            - ntasks (int, optional): Number of tasks per job, by default 1.
            - N (str, optional): The name of the job. If None, the script name without extension is used.
            - args (str or list, optional): Command-line arguments for the Python script, by default None.
            - sh_path (str, optional): Directory path where the job script will be saved. If None, current directory is used.
            - eo_path (str, optional): Path for the standard output and error log files, by default "/hom/sbnb/ddalton/area_52/scripts/run_log".
            - image (str, optional): Path to the Singularity image, by default "/home/sbnb/ddalton/singularity_images/cc_py37.simg".
            - cc_image (bool, optional): Flag indicating whether to use a specific Singularity image for ChemicalChecker, by default True.
            - os_remove (bool, optional): Flag to remove the job script file after submission, by default True.
            - partition (str, optional): Specifies a partition for the job, if needed, by default None.
            - exclude (str, optional): A list of partition to exclude from job allocation, by default None.

        """
        
        
        job_script_template = """\
#!/bin/bash
{options}

# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"
{commands}
"""

        if N is None:
            N = script_py.split("/")[-1].split(" ")[0].split(".py")[0]

        if args is not None:
            args_str = " ".join(f"${i}" for i in range(1, len(script_py.split()) + 1))
        else:
            args = ""
            args_str = " ".join(f"${i}" for i in range(1, len(script_py.split()) + 1))

        if sh_path is None:
            sh_path = os.getcwd()
        if eo_path is None:
            eo_path = os.getcwd()
        if not os.path.exists(eo_path):
            eo_path = os.path.join(os.getcwd(), eo_path)
            if not os.path.exists(eo_path):
                raise FileNotFoundError(f"Path {eo_path} does not exist.")

        if not os.path.exists(image):
            image = os.path.join(os.getcwd(), image)
            if not os.path.exists(image):
                raise FileNotFoundError(f"Singularity image {image} does not exist.")
        image = image.replace("/aloy/home", "/home/sbnb")

        options = f"""
#SBATCH --job-name={N}
#SBATCH --time={time}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}GB
#SBATCH --output={eo_path}{N}.%j.out
"""
        if partition:
            options += f"\n#SBATCH --partition={partition}"
        if exclude:
            options += f"\n#SBATCH --exclude={exclude}"

        commands = f"singularity exec {image} python {args_str}"

        job_script = job_script_template.format(options=options, commands=commands)

        jobname_sh = f"job_{str(uuid.uuid4())[:4]}.sh"
        jobname_sh_path = os.path.join(sh_path, jobname_sh)

        with open(jobname_sh_path, "w") as f:
            f.write(job_script)

        # once job_sh is created, we can adapt it to cluster directories
        __current_dir = os.getcwd().replace("/aloy/home", "/home/sbnb")
        jobname_sh_path = jobname_sh_path.replace("/aloy/home", "/home/sbnb")
        script_py = script_py.replace("/aloy/home", "/home/sbnb")
        
        
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            command = f"cd {__current_dir}; sbatch {jobname_sh_path} {script_py} {args}"
            logging.info(f"Running command: {command}")

            _stdin, _stdout, _stderr = self.ssh.exec_command(command)
            logging.info(_stdout.read().decode())
            logging.info(_stderr.read().decode())
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise
        finally:
            if self.ssh:
                self.ssh.close()
            if os_remove and os.path.exists(jobname_sh_path):
                os.remove(jobname_sh_path)
