from rdkit import Chem

import h5py

import numpy as np

import os

import pickle

import pybel

import sklearn

import sys

import tqdm

import pandas as pd

from standardiser import standardise





task_id = sys.argv[1]  # <TASK_ID>

filename = sys.argv[2]  # <FILE>  



input_pickle = pickle.load(open(filename, 'rb'))



count = input_pickle[task_id][0][0]

inchikeys = input_pickle[task_id][0][1]



# Read InChIs from the CC

df = pd.read_csv("/aloy/home/acomajuncosa/Aksel/CC_standardisation_standardiser/CC_MOLECULES.tsv")

ik_to_inchi = {i: j for i, j in zip(df['inchikey'], df['inchi'])}



### Standardisation ###



ik_to_std_smiles, ik_to_std_mol = {}, {}



for ik in inchikeys:



    # Standardise molecule

    try:

        mol = Chem.rdinchi.InchiToMol(ik_to_inchi[ik])[0]

        std_mol = standardise.run(mol, verbose=False)

        std_smiles = Chem.MolToSmiles(std_mol, isomericSmiles=True, canonical=True)

    except:

        std_mol, std_smiles = np.nan, np.nan



    # Save results

    ik_to_std_smiles[ik] = std_smiles

    ik_to_std_mol[ik] = std_mol



pickle.dump(ik_to_std_smiles, open("/aloy/home/acomajuncosa/Aksel/CC_standardisation_standardiser/results/ik_to_std_smiles_" + str(count) + ".pkl", "wb"))

pickle.dump(ik_to_std_mol, open("/aloy/home/acomajuncosa/Aksel/CC_standardisation_standardiser/results/ik_to_std_mol_" + str(count) + ".pkl", "wb"))