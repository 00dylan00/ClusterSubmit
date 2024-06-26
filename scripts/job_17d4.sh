#!/bin/bash

#SBATCH --job-name=jeje
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=60GB
#SBATCH --output=../scripts/logs/jeje.%j.out

#SBATCH --partition=aatd_gpu_4090

# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"
singularity exec /home/sbnb/ddalton/singularity_images/disease_sig.simg python $1 $2 $3 $4 $5 $6 $7 $8 $9 $10 $11 $12 $13 $14 $15 $16 $17 $18 $19 $20
