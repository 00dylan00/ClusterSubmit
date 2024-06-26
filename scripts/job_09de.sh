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
singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif python $1 $2 $3 $4 $5 $6 $7 $8 $9 $10 $11 $12 $13 $14 $15 $16 $17 $18 $19 $20
