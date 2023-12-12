#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A pipeline for perform covalent docking in an easy and smart way
"""
import gzip
import os
import socket
import argparse
import tempfile
import subprocess
import multiprocessing
from pathlib import Path
import importlib.resources

import cmder
import MolIO
import vstool

parser = argparse.ArgumentParser(prog='covalent-docking', description=__doc__.strip())
parser.add_argument('ligand', help="Path to a single SDF file contains ligands", type=vstool.check_file)
parser.add_argument('receptor', help="Path to a PDB file contains structure of receptor", type=vstool.check_file)
parser.add_argument('smarts', help="The SMARTS pattern for the ligand, i.e., C(=O)-O-C")
parser.add_argument('indices', help="The atom indices in the ligand file, i.e., 1,2")
parser.add_argument('residue', help="The residue name and number (Chain:ResNum), i.e., B:SER222")
parser.add_argument('--outdir', help="Path to a directory for saving output files", type=vstool.mkdir)
parser.add_argument('--batches', help="Number of batches the job needs to be split", type=int)

parser.add_argument('--nodes', type=int, default=0, help="Number of nodes, default: %(default)s.")
parser.add_argument('--email', help='Email address for send status change emails')
parser.add_argument('--email-type', help='Email type for send status change emails, default: %(default)s',
                    default='ALL', choices=('NONE', 'BEGIN', 'END', 'FAIL', 'REQUEUE', 'ALL'))
parser.add_argument('--delay', help='Hours need to delay running the job.', type=int, default=0)
parser.add_argument('--partition', help='Partition name of the job queue.')
parser.add_argument('--project', help='The nmme of project you would like to be charged.')
parser.add_argument('--hold', help='Only generate submit script but hold for submitting', action='store_true')

parser.add_argument('--debug', help='Enable debug mode (for development purpose).', action='store_true')
parser.add_argument('--verbose', help='Enable verbose mode.', action='store_true')
parser.add_argument('--quiet', help='Enable quiet mode.', action='store_true')
parser.add_argument('--version', version=vstool.get_version(__package__), action='version')

args = parser.parse_args()
logger = vstool.setup_logger(verbose=args.verbose, quiet=args.quiet)
script = importlib.resources.files(__package__) / f'{__package__}.sh'

setattr(args, 'nodes', 1 if args.debug and args.nodes else args.nodes)


def submit():
    hostname = socket.gethostname()
    ntasks_per_node = 1
    ntasks = args.nodes * ntasks_per_node
    partition = ('flex' if 'frontera' in hostname else 'vm-small') if args.debug else 'normal'
    partition = args.partition or partition

    cmds, code, job_id = [], 0, 0
    source = f'source {Path(vstool.check_exe("python")).parent}/activate\n\n'
    export = 'export PATH=/work/08944/fuzzy/share/software/openbabel/bin:${PATH}\n'
    cd = f'cd {args.outdir} || {{ echo "Failed to cd into {args.outdir}!"; exit 1; }}\n'

    cmd = ['batch-ligand', str(args.ligand), str(args.receptor), f"'{args.smarts}'", f"'{args.indices}'",
           f"'{args.residue}'", str(args.outdir), f'--batch {args.batches or ntasks * 8}']
    if args.debug:
        cmd.append('--debug')
    cmd = export + source + cd + ' \\\n  '.join(cmd)
    cmds.append(f'{cmd}\n')

    lcmd = ['module load launcher', 'export LAUNCHER_WORKDIR={outdir}',
            'export LAUNCHER_JOB_FILE={outdir}/{job}.commands.txt', '"${{LAUNCHER_DIR}}"/paramrun', '']
    lcmd = '\n'.join(lcmd).format(outdir=str(args.outdir), job='docking')
    cmds.append(lcmd)

    cmds.append(f'post-docking {args.outdir} --debug' if args.debug else f'post-docking {args.outdir}')
    vstool.submit('\n'.join(cmds),
                  nodes=args.nodes, ntasks=ntasks, ntasks_per_node=ntasks_per_node,
                  job_name='covalent', day=0 if args.debug else 1,
                  hour=1 if args.debug else 23, minute=50, partition=partition, email=args.email,
                  mail_type=args.email_type, log='covalent.docking.log',
                  script=args.outdir / 'submit.sh',
                  delay=args.delay, project=args.project, hold=args.hold)


def dlg2sdf(dlg, sdf=None, title=''):
    s = ''.join(f'{item.sdf(title=title)}' for item in MolIO.parse_dlg(dlg))
    if sdf is None:
        return s
    else:
        sdf = sdf or str(Path(dlg).with_suffix('.sdf'))
        with open(sdf, 'w') as o:
            o.write(s)
        return sdf


def dock(ligand, receptor='', residue='', smarts='', indices=''):
    ligand = Path(ligand)
    output = ligand.parent.parent / f'{ligand.parent.name}.sdf'
    if output.exists():
        logger.debug(f'Docking results for {ligand} already exist, skip re-docking')
        return str(output)
    else:
        log = ligand.parent / 'covalent.log'
        cmd = f"{script} {ligand} {receptor} '{smarts}' '{indices}' '{residue}' {ligand.parent} &> {log}"
        try:
            p = cmder.run(cmd, timeout=900, fmt_cmd=False)
            if p.returncode:
                logger.error(f'Docking {ligand} failed')
                output = ''
            else:
                try:
                    dlg2sdf(str(ligand.parent / 'ligand_covalent.dlg'), output, title=ligand.parent.name)
                    cmder.run(f'rm -rf {ligand.parent}')
                except Exception as e:
                    logger.error(f'Failed to parse docking results from {ligand.parent} due to {e}')
                    return ''
        except subprocess.TimeoutExpired as e:
            logger.error(f'Docking {ligand} failed due to timeout (900s)')
            output = ''

        return str(output)


def main():
    if args.nodes:
        setattr(args, 'output', args.outdir / 'covalent.docking.sdf.gz')
        if args.output.exists():
            vstool.debug_and_exit(f'Covalent docking result {args.output} already exists, skip re-submitting')
        submit()
    else:
        output = args.ligand.with_suffix('.docking.sdf.gz')
        if output.exists():
            vstool.debug_and_exit(f'Covalent docking result {output} already exists, skip re-processing')

        if os.environ.get('SLURM_JOB_ID', ''):
            wd = vstool.mkdir(tempfile.mkdtemp(prefix='covalent.', suffix='.docking'))
            partition = os.environ.get('SLURM_JOB_PARTITION', 'vm-small')
            if partition == 'vm-small':
                cpus = 16
            elif partition == 'gpu-a100-small':
                cpus = 32
            else:
                cpus = multiprocessing.cpu_count() - 1
            try:
                logger.debug(f'Individualizing ligands in {args.ligand}')
                ligands = []
                for i, s in enumerate(MolIO.parse_sdf(args.ligand)):
                    if s.mol:
                        if args.debug and i == 2 * cpus:
                            break
                        d = vstool.mkdir(wd / s.title)
                        ligands.append(s.sdf(output=d / f'{s.title}.sdf'))
                logger.debug(f'Saved {len(ligands):,} SDF files to {wd}')
                
                if ligands:
                    cpus = min(cpus, len(ligands))
                    logger.info(f'Docking {len(ligands):,} ligands in {args.ligand} with {cpus} CPUs')
                    outs = vstool.parallel_cpu_task(dock, ligands, processes=cpus, chunksize=1,
                                                    receptor=str(args.receptor), residue=args.residue, 
                                                    smarts=args.smarts, indices=args.indices)
                else:
                    vstool.debug_and_exit(f'No ligands was found in {args.ligand}, no docking was performed')

                logger.debug(f'Concatenating docking results to {output}')
                n = 0
                with gzip.open(output, 'wt') as o:
                    for out in outs:
                        if out:
                            with open(out) as f:
                                o.write(f.read())
                            n += 1
                logger.info(f'Successfully concatenated docking results for {n:,} ligands')

            except Exception as e:
                vstool.error_and_exit(f'Covalent docking failed due to:\n{e}\n\n{traceback.format_exc()}')
            finally:
                if args.debug:
                    logger.info(f'Temporary directory {wd} was not deleted due to debug mode was enabled')
                else:
                    cmder.run(f'rm -rf {wd}')
        else:
            logger.error('You are not on a compute node not did not submit docking to the queue, '
                         'directly running docking on login node is prohibited')


if __name__ == '__main__':
    main()
