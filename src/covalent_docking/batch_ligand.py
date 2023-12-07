#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A command line tool for easily generating ligand batches
"""

import json
import os
import sys
import argparse
import traceback
from pathlib import Path

import cmder
import MolIO
import vstool
from loguru import logger

parser = argparse.ArgumentParser(prog='batch-ligand', description=__doc__.strip())
parser.add_argument('ligand', help="Path to a single SDF file contains ligands", type=vstool.check_file)
parser.add_argument('receptor', help="Path to a PDB file contains structure of receptor", type=vstool.check_file)
parser.add_argument('smarts', help="The SMARTS pattern for the ligand, i.e., C(=O)-O-C")
parser.add_argument('indices', help="The atom indices in the ligand file, i.e., 1,2")
parser.add_argument('residue', help="The residue name and number (Chain:ResNum), i.e., B:SER222")
parser.add_argument('scratch', help='Path to the scratch directory', type=vstool.mkdir)

parser.add_argument('--batch', type=int, help="Number of batches that the SDF will be split to, "
                                              "default: %(default)s", default=4, required=True)
parser.add_argument('--debug', help='Enable debug mode (for development purpose).', action='store_true')

args = parser.parse_args()
vstool.setup_logger(verbose=True)


def main():
    logger.debug(f'Splitting {args.ligand} into {args.batch} batches ...')
    batches = MolIO.batch_sdf(args.ligand, args.batch, f'{args.scratch}/batch.')

    program = Path(vstool.check_exe("python")).parent / 'covalent-docking'
    
    with args.scratch.joinpath('docking.commands.txt').open('w') as o:
        for batch in batches:
            cmd = f"{program} {batch} {args.receptor} '{args.smarts}' '{args.indices}' '{args.residue}'"
            if args.debug:
                cmd = f'{cmd} --debug'
            o.write(f'{cmd}\n')
        logger.debug(f'Docking commands were saved to {o.name}')


if __name__ == '__main__':
    main()
