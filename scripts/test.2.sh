#!/bin/bash
# Options for sbatch
##SBATCH --chdir=/aloy/home/bsaldivar/hVAE/hvae_latent_is_signature_4/logs/
#SBATCH --output=../scripts/logs/jeje.%j.out
#SBATCH -p sbnb-gpu
#SBATCH --array=1-1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=10G
#SBATCH --qos=long
#SBATCH -J TrJDL0
# End of sbatch

source /apps/manual/software/Singularity/3.9.6/etc/profile
# CUDA drivers
#export LD_LIBRARY_PATH=/apps/manual/software/CUDA/11.6.1/lib64:/apps/manual/software/CUDA/11.6.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/11.6.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/11.6.1/nvvm/lib64/:/apps/manual/software/CUDNN/8.3.2/lib:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/apps/manual/software/CUDA/11.6.1/lib64:/apps/manual/software/CUDA/11.6.1/targets/x86_64-linux/lib:/apps/manual/software/CUDA/11.6.1/extras/CUPTI/lib64/:/apps/manual/software/CUDA/11.6.1/nvvm/lib64/:$LD_LIBRARY_PATH
export SINGULARITYENV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH #/.singularity.d/libs
export SINGULARITY_BINDPATH="/aloy/home,/aloy/data,/aloy/scratch,/aloy/web_checker,/aloy/web_repository"
export SINGULARITY_TMPDIR=/aloy/home/bsaldivar/scratch/

singularity exec --cleanenv --nv /aloy/home/bsaldivar/hVAE/hVAE.simg python test.py