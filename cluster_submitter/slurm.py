import paramiko, uuid
import os
import logging
import random
from .motivation import shreck_quotes  # Assume it's an external module

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s')

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


    def submit_job(self, script_py, time, mem, cpus, n_array=None,gpus=None, N=None, args=None,
                   sh_path=None, eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   image="/aloy/home/ddalton/singularity_images/cc_py37.simg", cc_image=True,
                   os_remove=True, partition=None, exclude=None):
        """
        Submits a job to an HPC cluster using Slurm.

        Args:
            - script_py (str): The path to the Python script to be executed.
            - time (str): The wall time for the job in the format 'HH:MM:SS'.
            - mem (int): The amount of memory required for the job in GB.
            - cpus (int): The number of CPU cores to allocate for the job.
            - n_array (int, optional): Defines the nº of jobs for a given array.
            - ntasks (int, optional): Number of tasks per job, by default 1.
            - N (str, optional): The name of the job. If None, the script name without extension is used.
            - args (str or list, optional): Command-line arguments for the Python script, by default None.
            - sh_path (str, optional): Directory path where the job script will be saved. If None, current directory is used.
            - eo_path (str, optional): Path for the standard output and error log files, by default "/hom/sbnb/ddalton/area_52/scripts/run_log".
            - image (str, optional): Path to the Singularity image, by default "/aloy/home/ddalton/singularity_images/cc_py37.simg".
            - cc_image (bool, optional): Flag indicating whether to use a specific Singularity image for ChemicalChecker, by default True.
            - os_remove (bool, optional): Flag to remove the job script file after submission, by default True.
            - partition (str, optional): Specifies a partition for the job, if needed, by default None.
            - exclude (str, optional): A list of partition to exclude from job allocation, by default None.

        """
        # set as variable for all
        self.eo_path = eo_path

        max_jobs = 1000
        if n_array:
            n_jobs = n_array // max_jobs
            n_jobs_last = n_array % max_jobs
            for i in range(n_jobs):
                self._submit_single_job(script_py, time, mem, cpus, array=f"1-{max_jobs}", offset=i*max_jobs, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, image=image, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)
            
            if n_jobs_last:
                self._submit_single_job(script_py, time, mem, cpus, array=f"1-{n_jobs_last}", offset=n_jobs*max_jobs, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, image=image, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)
        
        else:
            self._submit_single_job(script_py, time, mem, cpus, array=None, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, image=image, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)


    def _submit_single_job(self, script_py, time, mem, cpus, array=None, offset=None, gpus=None, N=None, args=None,
                   sh_path=None, eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   image="/aloy/home/ddalton/singularity_images/cc_py37.simg", cc_image=True,
                   os_remove=True, partition=None, exclude=None):
        
        """
        Submits a job to an HPC cluster using Slurm.

        Args:
            - script_py (str): The path to the Python script to be executed.
            - time (str): The wall time for the job in the format 'HH:MM:SS'.
            - mem (int): The amount of memory required for the job in GB.
            - cpus (int): The number of CPU cores to allocate for the job.
            - array (str, optional): Defines a job array, by default "1-1".
            - N (str, optional): The name of the job. If None, the script name without extension is used.
            - args (str or list, optional): Command-line arguments for the Python script, by default None.
            - sh_path (str, optional): Directory path where the job script will be saved. If None, current directory is used.
            - eo_path (str, optional): Path for the standard output and error log files, by default "/hom/sbnb/ddalton/area_52/scripts/run_log".
            - image (str, optional): Path to the Singularity image, by default "/aloy/home/ddalton/singularity_images/cc_py37.simg".
            - cc_image (bool, optional): Flag indicating whether to use a specific Singularity image for ChemicalChecker, by default True.
            - os_remove (bool, optional): Flag to remove the job script file after submission, by default True.
            - partition (str, optional): Specifies a partition for the job, if needed, by default None.
            - exclude (str, optional): A list of partition to exclude from job allocation, by default None.

        TO DO:
            - SBATCH --ntasks

        """
        
        
        job_script_template = """\
#!/bin/bash
{options}

{array_config}

{gpu_config}

cd {script_dir}


# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/aloy/home"
{commands}
"""

        if N is None:
            N = script_py.split("/")[-1].split(" ")[0].split(".py")[0]
        self.N = N
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

        image = image
        eo_path = os.path.abspath(eo_path)

        options = f"""
#SBATCH --job-name={N}
#SBATCH --time={time}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}GB
#SBATCH --output={eo_path}/{N}.%j.out
"""

        gpu_config = ""
        commands = f"singularity exec {image} python {args_str}"
        if partition:
            options += f"\n#SBATCH --partition={partition}"
        if exclude:
            options += f"\n#SBATCH --exclude={exclude}"

        if gpus:
            options += f"\n#SBATCH --gpus={gpus}"
            commands = f"singularity exec --cleanenv --nv {image} python {args_str}"
            gpu_config = """
# Source LMOD
# Necessary for using `module` - this when using 
# paramiko is not loaded
source /etc/profile.d/z00-lmod.sh

# CUDA drivers
module load CUDA/12.0.0"""         

        array_config = ""
        if array:
            options += f"\n#SBATCH --array={array}"
            commands += " $SLURM_ARRAY_TASK_ID"
            if not offset:
                offset = 0
            array_config = f"""
# Manually offset the SLURM_ARRAY_TASK_ID
OFFSET={offset}
TASK_ID=$(($SLURM_ARRAY_TASK_ID + $OFFSET))
"""


        script_dir = os.path.dirname(script_py)
        if len(script_dir) == 0:
            script_dir = os.getcwd()

        job_script = job_script_template.format(options=options,gpu_config=gpu_config,script_dir=script_dir, array_config=array_config,commands=commands)

        jobname_sh = f"job_{str(uuid.uuid4())[:4]}.sh"
        jobname_sh_path = os.path.join(sh_path, jobname_sh)

        with open(jobname_sh_path, "w") as f:
            f.write(job_script)

        # once job_sh is created, we can adapt it to cluster directories
        jobname_sh_absolute_path = os.path.abspath(jobname_sh_path)
        script_py = os.path.abspath(script_py)
        
        
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            # command = f"cd {__current_dir}; sbatch {jobname_sh_path} {script_py} {args}"
            command = f"sbatch {jobname_sh_absolute_path} {script_py} {args}"
            logging.info(f"Running command: {command}")

            _stdin, _stdout, _stderr = self.ssh.exec_command(command)
            output_message = _stdout.read().decode().strip()
            logging.info(output_message)
            logging.info(_stderr.read().decode())
            self.job_id = output_message.split()[-1]

            # safely rename the bash script to the job_id ! !
            jobname_sh_path_new = os.path.join(sh_path, f"job_{self.job_id}.sh")
            logging.debug(f"Renaming {jobname_sh_path} to {jobname_sh_path_new}")

            os.rename(jobname_sh_path, jobname_sh_path_new)

        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise
        finally:
            if self.ssh:
                self.ssh.close()
            if os_remove and os.path.exists(jobname_sh_path_new):
                os.remove(jobname_sh_path_new)


    def get_status(self):
        """Get the status of the submitted job."""
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            # command = f"cd {__current_dir}; sbatch {jobname_sh_path} {script_py} {args}"
            command = f"squeue -u {self.username}"
            logging.info(f"Running command: {command}")

            _stdin, _stdout, _stderr = self.ssh.exec_command(command)
            logging.info(_stdout.read().decode())
            logging.info(_stderr.read().decode())
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise e

    def cancel(self):
        """Cancel a specific job submitted by the user."""
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            # command = f"cd {__current_dir}; sbatch {jobname_sh_path} {script_py} {args}"
            command = f"scancel {self.job_id}"
            logging.info(f"Running command: {command}")

            _stdin, _stdout, _stderr = self.ssh.exec_command(command)
            logging.info(_stdout.read().decode())
            logging.info(_stderr.read().decode())

        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise e


    def cancel_all(self):
        """Cancel ALL jobs submitted by the user."""
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            # command = f"cd {__current_dir}; sbatch {jobname_sh_path} {script_py} {args}"
            command = f"scancel -u {self.username}"
            logging.info(f"Running command: {command}")

            _stdin, _stdout, _stderr = self.ssh.exec_command(command)
            logging.info(_stdout.read().decode())
            logging.info(_stderr.read().decode())
        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise e

    def logs(self):
        """Print the logs of the submitted job.
        For that open the output and error log files."""

        from time import sleep

        
        output_path = os.path.join(self.eo_path,f"{self.N}.{self.job_id}.out")
        
        for i in range(10):
        
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    logging.info(f"Output log file: {output_path}")
                    print(f.read())
                return
            print(f"Waiting for output log file to be created {i}s /20s . . .", end="\r")    
            sleep(1)
        
        logging.error(f"Output log file {output_path} not found.")
        
# this used to be necessary for GPU !
# export LD_LIBRARY_PATH=/apps/manual/software/CUDA/12.1/lib64:/apps/manual/software/CUDA/12.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/12.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/12.1/nvvm/lib64/:$LD_LIBRARY_PATH
    
        