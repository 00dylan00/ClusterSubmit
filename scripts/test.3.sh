#!/bin/bash
# Options for sbatch
#SBATCH --output=logs/%x.%j.out
#SBATCH --partition=irb_gpu_3090
# #SBATCH -p sbnb-gpu
#SBATCH --array=1-1
#SBATCH --gpus=4
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --time=20:00:00

cd /home/sbnb/ddalton/projects/scFoundation/model/

singularity exec --cleanenv --nv  /home/sbnb/ddalton/singularity_images/scfoundation.sif python "$@"
