#!/bin/bash

#SBATCH --output=logs/%x.%j.out
#SBATCH --partition=irb_gpu_3090
#SBATCH --gpus=6
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=20:00:00



# CUDA drivers
# export LD_LIBRARY_PATH=/apps/manual/software/CUDA/11.6.1/lib64:/apps/manual/software/CUDA/11.6.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/11.6.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/11.6.1/nvvm/lib64/:$LD_LIBRARY_PATH

# for DB servers connection

# Install packages
# singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif pip install scanpy
# singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif pip install einops
# singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif pip install local-attention   
# singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116


# Change to the correct directory
# cd /home/sbnb/ddalton/projects/scFoundation/model/

# Execute the Python script
# singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif python "$@"
singularity exec --nv /home/sbnb/bsaldivar/hVAE/hVAE.simg python test.py
