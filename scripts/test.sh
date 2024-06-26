#!/bin/bash

#SBATCH --job-name=jeje
#SBATCH --time=20:00:00
#SBATCH --cpus-per-task=20
#SBATCH --mem=120GB
#SBATCH --output=../scripts/logs/jeje.%j.out

#SBATCH --partition=irb_gpu_3090
#SBATCH --gpus=1


# CUDA drivers
export LD_LIBRARY_PATH=/apps/manual/software/CUDA/11.6.1/lib64:/apps/manual/software/CUDA/11.6.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/11.6.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/11.6.1/nvvm/lib64/:$LD_LIBRARY_PATH

# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"

# Install packages
singularity exec /home/sbnb/ddalton/singularity_images/disease_sig.simg pip install scanpy
singularity exec /home/sbnb/ddalton/singularity_images/disease_sig.simg pip install einops
singularity exec /home/sbnb/ddalton/singularity_images/disease_sig.simg pip install local-attention   
# singularity exec /home/sbnb/bsaldivar/hVAE/hVAE.simg pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116

# Set PYTHONPATH to include the user's local library directory
export PYTHONPATH=$PYTHONPATH:/home/sbnb/ddalton/.local/lib/python3.10/site-packages


# Change to the correct directory
cd /home/sbnb/ddalton/projects/scFoundation/model/

# Execute the Python script
singularity exec /home/sbnb/bsaldivar/hVAE/hVAE.simg python "$@"