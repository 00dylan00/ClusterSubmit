# ClusterSubmit

<div style="text-align: center;">
    <img src="ClusterSubmit.dalle.webp" alt="ClusterSubmit" width="50%" height="50%">
</div>

ClusterSubmit is a Python tool designed to simplify the submission of computational jobs to High-Performance Computing (HPC) clusters. It supports job submission through both Slurm and Sun Grid Engine (SGE) workload managers. With ClusterSubmit, users can easily configure and submit jobs, manage resource allocation, and monitor job progress.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Examples](#examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Features
- **Support for Multiple Workload Managers**: Submit jobs to both Slurm and SGE.
- **Flexible Job Configuration**: Easily configure job parameters such as runtime, memory, CPUs, and more.
- **Automated Script Generation**: Automatically generate job scripts based on provided parameters.
- **Secure SSH Connections**: Use `paramiko` to securely connect to HPC clusters.
- **Logging and Error Handling**: Detailed logging for monitoring job submission and execution.

## Requirements
- Python 3.6 or higher
- `paramiko` for SSH connections
- Access to an HPC cluster with Slurm or SGE

## Installation
Clone the repository and install the necessary dependencies:

```bash
git clone https://github.com/00dylan00/ClusterSubmit.git
cd ClusterSubmit
pip install -r requirements.txt
```

## Configuration
Create a configuration file based on the example provided in documentation/example_config.py. This file should include details for your HPC cluster such as the host, username, password, and default job settings.

```python
# example_config.py

CONFIG = {
    'host': 'your_hpc_host',
    'username': 'your_username',
    'password': 'your_password',
    'default_options': {
        'time': '01:00:00',  # Default job time
        'mem': 4,            # Default memory in GB
        'cpus': 2,           # Default number of CPUs
    }
}
```
## Usage

ClusterSubmit can be used to submit jobs by creating a Slurm or SGE job submission instance and then calling the submit_job method with the appropriate parameters.
Submitting a Job with Slurm.

```python

from cluster_submitter.slurm import Slurm

# Create a Slurm job submission instance
slurm = Slurm(host='your_hpc_host', username='your_username', password='your_password')

# Submit a job
slurm.submit_job(
    script_py='path/to/your_script.py',
    time='02:00:00',
    mem=8,
    cpus=4,
    partition='general',
    N='my_job',
    args='--arg1 value1 --arg2 value2'
)
```

## Submitting a Job with SGE

```python
from cluster_submitter.sungrid import SunGrid

# Create an SGE job submission instance
sge = SunGrid(host='your_hpc_host', username='your_username', password='your_password')

# Submit a job
sge.submit_job(
    script_py='path/to/your_script.py',
    time='03:00:00',
    mem=16,
    cpus=8,
    N='my_sge_job',
    args='--arg1 value1 --arg2 value2'
)
```

## Examples

For more detailed examples and a tutorial, please refer to the Jupyter notebook in documentation/tutorial.ipynb.



