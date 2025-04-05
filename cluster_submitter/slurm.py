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


    def submit_job(self, script_py:str, time:str, mem:int, cpus:int, n_array:int=None, n_concurrent:int=None, gpus:int=None, N:str=None, args:str=None,
                   sh_path:str=None, eo_path:str="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   singularity_image:str=None, 
                   conda_env:str=None, 
                   cc_image:bool=True,
                   os_remove:bool=True, partition:str=None, exclude:str=None):
        """
        Submits a job to an HPC cluster using Slurm.

        Args:
            - script_py (str): The path to the Python script to be executed.
            - time (str): The wall time for the job in the format 'HH:MM:SS'.
            - mem (int): The amount of memory required for the job in GB.
            - cpus (int): The number of CPU cores to allocate for the job.
            - n_array (int, optional): Defines the nº of jobs for a given array.
            - n_concurrent (int, optional): Defines the nº of concurrent jobs.
            - ntasks (int, optional): Number of tasks per job, by default 1.
            - N (str, optional): The name of the job. If None, the script name without extension is used.
            - args (str or list, optional): Command-line arguments for the Python script, by default None.
            - sh_path (str, optional): Directory path where the job script will be saved. If None, current directory is used.
            - eo_path (str, optional): Path for the standard output and error log files, by default "/hom/sbnb/ddalton/area_52/scripts/run_log".
            - singularity_image (str, optional): Path to the Singularity image
            - conda_env (str, optional): Name of the conda environment to activate, by default None.
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
                array_params = f"1-{max_jobs}%{n_concurrent}" if n_concurrent else f"1-{max_jobs}"
                self._submit_single_job(script_py, time, mem, cpus, array=array_params, offset=i*max_jobs, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, singularity_image=singularity_image, conda_env=conda_env, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)
            
            if n_jobs_last:
                array_params = f"1-{n_jobs_last}%{n_concurrent}" if n_concurrent else f"1-{max_jobs}"
                self._submit_single_job(script_py, time, mem, cpus, array=array_params, offset=n_jobs*max_jobs, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, singularity_image=singularity_image, conda_env=conda_env, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)
        
        else:
            self._submit_single_job(script_py, time, mem, cpus, array=None, gpus=gpus, N=N, args=args,
                   sh_path=sh_path, eo_path=eo_path, singularity_image=singularity_image, conda_env=conda_env, cc_image=cc_image,
                   os_remove=os_remove, partition=partition, exclude=exclude)


    def _submit_single_job(self, script_py, time, mem, cpus, array=None, offset=None, gpus=None, N=None, args=None,
                   sh_path=None, eo_path="/hom/sbnb/ddalton/area_52/scripts/run_log",
                   singularity_image:str=None,
                   conda_env:str=None,
                   cc_image=True,
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
            - singularity_image (str, optional): Path to the Singularity image, by default None. 
            - conda_env (str, optional): Name of the conda environment to activate, by default None.
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
"""
        if singularity_image is not None:
            job_script_template += """
# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb:/aloy/home,/data/sbnb/data:/aloy/data,/data/sbnb/scratch:/aloy/scratch,/data/sbnb/chemicalchecker:/aloy/web_checker,/data/sbnb/web_updates:/aloy/web_repository"
{commands}
"""
            image = singularity_image
        elif conda_env is not None:
            job_script_template += """
module load anaconda3
conda activate {conda_env}
{commands}
"""
            image = conda_env
        else: 
            raise ValueError("Either singularity_image or conda_env must be provided.")
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

        eo_path = os.path.abspath(eo_path)

        options = f"""
#SBATCH --job-name={N}
#SBATCH --time={time}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}GB
#SBATCH --output={eo_path}/{N}.%j.out
"""

        gpu_config = "source /etc/profile.d/z00-lmod.sh"
        
        if partition:
            options += f"\n#SBATCH --partition={partition}"
        if exclude:
            options += f"\n#SBATCH --exclude={exclude}"

        assert (singularity_image is not None) ^ (conda_env is not None), "Provide only one: either 'singularity_image' or 'conda_env'."
        if singularity_image is not None:
            commands = f"singularity exec {image} python {args_str}"
            if gpus:
                options += f"\n#SBATCH --gpus={gpus}"
                commands = f"singularity exec --cleanenv --nv {image} python {args_str}"
                if self.host == 'irblogin01.irbbarcelona.pcb.ub.es':
                    gpu_config = """
# Source LMOD
# Necessary for using `module` - this when using 
# paramiko is not loaded
source /etc/profile.d/z00-lmod.sh

# CUDA drivers
module load CUDA/12.0.0"""
                elif self.host == 'hpclogin1':
                    gpu_config = """
# Source LMOD
# Necessary for using `module` - this when using 
# paramiko is not loaded
source /etc/profile.d/z00_lmod.sh

# CUDA drivers
#module load CUDA/12.0.0

# CUDA 12.0.0 not available - load 11.6.1
export LD_LIBRARY_PATH=/apps/manual/software/CUDA/11.6.1/lib64:/apps/manual/software/CUDA/11.6.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/11.6.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/11.6.1/nvvm/lib64/:$LD_LIBRARY_PATH
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH #/.singularity.d/libs
export SINGULARITY_BINDPATH="/aloy/home,/aloy/data,/aloy/scratch,/aloy/web_checker,/aloy/web_repository"
"""                         
        if conda_env is not None:
            commands = f"python {args_str}"

        array_config = ""
        if array:
            options += f"\n#SBATCH --array={array}"
            commands += " $TASK_ID"
            if not offset:
                offset = 0
            array_config = f"""
# Manually offset the SLURM_ARRAY_TASK_ID
OFFSET={offset}
TASK_ID=$(($SLURM_ARRAY_TASK_ID + $OFFSET))
"""

        script_dir = os.path.dirname(script_py.split(" ")[0])
        if len(script_dir) == 0:
            script_dir = os.getcwd()

        if conda_env is not None:
            job_script = job_script_template.format(options=options,gpu_config=gpu_config,script_dir=script_dir, array_config=array_config,conda_env=conda_env, commands=commands)
        else:
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
        
        for i in range(20):
        
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    logging.info(f"Output log file: {output_path}")
                    print(f.read())
                return
            print(f"Waiting for output log file to be created {i}s /20s . . .", end="\r")    
            sleep(1)
        
        logging.error(f"Output log file {output_path} not found.")

    def get_info(self):
        """
        Retrieves detailed information about the HPC cluster nodes, including CPU, memory, GPU usage, and partitions.
        """
        try:
            logging.info(random.choice(shreck_quotes))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.host, username=self.username, password=self.password)

            # Command to retrieve basic node information
            sinfo_command = "sinfo -N -o '%N %P %C %G'"
            _stdin, _stdout, _stderr = self.ssh.exec_command(sinfo_command)
            sinfo_output = _stdout.read().decode().strip().splitlines()[1:]  # Skip header
            error_output = _stderr.read().decode().strip()

            if error_output:
                logging.error(f"Error while fetching node info: {error_output}")
                return

            node_data = []
            for line in sinfo_output:
                parts = line.split()
                node_name = parts[0]
                partitions = parts[1]
                cpus_info = parts[2]
                gpus_info = parts[3] if parts[3] != "(null)" else "-"
                node_data.append((node_name, partitions, cpus_info, gpus_info))

            # Fetch detailed memory and GPU information for each node
            detailed_info = []
            for node_name, partitions, cpus_info, gpus_info in node_data:
                scontrol_command = f"scontrol show node {node_name}"
                _stdin, _stdout, _stderr = self.ssh.exec_command(scontrol_command)
                scontrol_output = _stdout.read().decode()

                logging.debug(f"scontrol output for {node_name}: {scontrol_output}")

                # Extract memory details
                total_memory = int(self._extract_value(scontrol_output, "RealMemory", default="0"))
                allocated_memory = int(self._extract_value(scontrol_output, "AllocMem", default="0"))
                free_memory = int(self._extract_value(scontrol_output, "FreeMem", default="0"))

                # Convert memory to GB
                total_memory_gb = total_memory // 1024
                allocated_memory_gb = allocated_memory // 1024
                free_memory_gb = free_memory // 1024

                memory_formatted = f"{allocated_memory_gb}/{total_memory_gb}/{free_memory_gb}GB"

                # Extract GPU details (use default if keys are missing)
                gpu_total = self._safe_extract_gpu(scontrol_output, "Gres=gpu")
                gpu_allocated = self._safe_extract_gpu(scontrol_output, "AllocTRES=gpu")
                gpu_free = max(0, gpu_total - gpu_allocated)

                gpu_formatted = f"{gpu_allocated}/{gpu_total}/{gpu_free}"

                detailed_info.append(f"{node_name}\t{cpus_info}\t{memory_formatted}\t{gpu_formatted}\t{partitions}")

            # Log the results in a formatted table
            logging.info("Node Information (A: Allocated, T: Total, F: Free):")
            logging.info("Node\tCPUs(A/F/O/T)\tMemory(A/T/F)\tGPUs(A/T/F)\tPartitions")
            for line in detailed_info:
                print(line)

        except paramiko.SSHException as e:
            logging.error(f"Unable to establish SSH connection: {e}")
            raise
        finally:
            if self.ssh:
                self.ssh.close()

    def _extract_value(self, output, key, splitter="=", default=None):
        """
        Utility function to extract a specific value from the scontrol output.

        Args:
            output (str): The output string from scontrol.
            key (str): The key to search for.
            splitter (str): The delimiter used to split the key-value pair.
            default: The default value to return if the key is not found.

        Returns:
            str or default: The extracted value or the default if the key is not found.
        """
        try:
            line = next((line for line in output.splitlines() if key in line), None)
            if line:
                return line.split(splitter)[-1].strip()
            return default
        except Exception as e:
            logging.warning(f"Error extracting value for key '{key}': {e}")
            return default

    def _safe_extract_gpu(self, output, key):
        """
        Safely extract GPU details from scontrol output, returning 0 if unavailable.

        Args:
            output (str): The output string from scontrol.
            key (str): The key to search for in the output.

        Returns:
            int: The extracted value or 0 if the key is not found or an error occurs.
        """
        try:
            line = next((line for line in output.splitlines() if key in line), None)
            if line:
                value = line.split(":")[-1].strip().split("=")[-1]
                return int(value)
        except Exception:
            return 0
        return 0


# this used to be necessary for GPU !
# export LD_LIBRARY_PATH=/apps/manual/software/CUDA/12.1/lib64:/apps/manual/software/CUDA/12.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/12.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/12.1/nvvm/lib64/:$LD_LIBRARY_PATH
    
        