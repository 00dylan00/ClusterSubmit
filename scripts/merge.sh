#!/bin/bash

#SBATCH --job-name=merge_thingies
#SBATCH --time=20:00:00
#SBATCH --cpus-per-task=12
#SBATCH --mem=200GB
#SBATCH --output=../scripts/logs/merge_thingies.%j.out


cd /home/sbnb/ddalton/projects/disease_signatures/scripts

# for DB servers connection
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export SINGULARITY_BINDPATH="/home/sbnb"
singularity exec /home/sbnb/ddalton/singularity_images/scfoundation.sif python $1
