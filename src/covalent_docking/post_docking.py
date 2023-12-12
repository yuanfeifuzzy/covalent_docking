#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A command line tool for pst-docking analysis
"""

import json
import os
import sys
import argparse
import traceback
from pathlib import Path
from multiprocessing import cpu_count

import cmder
import MolIO
import vstool

parser = argparse.ArgumentParser(prog='post-docking', description=__doc__.strip())
parser.add_argument('wd', help="Path to a directory contains docking output", type=vstool.check_dir)

parser.add_argument('--debug', help='Enable debug mode (for development purpose).', action='store_true')
parser.add_argument('--version', version=vstool.get_version(__package__), action='version')

args = parser.parse_args()
logger = vstool.setup_logger(verbose=True)


def main():
    output = args.wd / 'covalent.docking.sdf.gz'
    if output.exists():
        logger.debug(f'Covalent docking results {output} already exists, skip re-processing')
    else:
        cmder.run(f'cat {args.wd}/batch.*[0-9].docking.sdf.gz > {output}', exit_on_error=True)
        logger.debug(f'Successfully saved docking results to {output}')
        if not args.debug:
            cmder.run(f'rm {args.wd}/batch.*[0-9].docking.sdf.gz')
            cmder.run(f'rm {args.wd}/batch.*[0-9].sdf')


if __name__ == '__main__':
    main()
