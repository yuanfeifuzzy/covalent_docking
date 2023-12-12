# Covalent Docking

A pipeline for perform covalent docking in an easy and smart way on TACC.

## Usage
### Activate the virtual environment
```shell
$ source /work/08944/fuzzy/share/software/covalent-docking
```

### Check the help message of `covalent-docking` utility
```shell
$ covalent-docking -h
usage: covalent-docking [-h] [--outdir OUTDIR] [--batches BATCHES] [--nodes NODES] [--email EMAIL] [--email-type {NONE,BEGIN,END,FAIL,REQUEUE,ALL}] [--delay DELAY] [--partition PARTITION] [--project PROJECT] [--hold] [--debug] [--verbose] [--quiet] [--version] ligand receptor smarts indices residue

A pipeline for perform covalent docking in an easy and smart way

positional arguments:
  ligand                Path to a single SDF file contains ligands
  receptor              Path to a PDB file contains structure of receptor
  smarts                The SMARTS pattern for the ligand, i.e., C(=O)-O-C
  indices               The atom indices in the ligand file, i.e., 1,2
  residue               The residue name and number (Chain:ResNum), i.e., B:SER222

options:
  -h, --help            show this help message and exit
  --outdir OUTDIR       Path to a directory for saving output files
  --batches BATCHES     Number of batches the job needs to be split
  --nodes NODES         Number of nodes, default: 0.
  --email EMAIL         Email address for send status change emails
  --email-type {NONE,BEGIN,END,FAIL,REQUEUE,ALL}
                        Email type for send status change emails, default: ALL
  --delay DELAY         Hours need to delay running the job.
  --partition PARTITION
                        Partition name of the job queue.
  --project PROJECT     The nmme of project you would like to be charged.
  --hold                Only generate submit script but hold for submitting
  --debug               Enable debug mode (for development purpose).
  --verbose             Enable verbose mode.
  --quiet               Enable quiet mode.
  --version             show program's version number and exit

```

### Run `colvalent-docking` utility with required and/or optional arguments, i.e.
```shell
$ covalent-docking \
  /work/08944/fuzzy/share/chemical_library/covalent_docking/Enamine_Covalent_Compounds_SulfonylFloride_Fluorosulfates_20230811_3d.sdf \
  /work/08944/fuzzy/share/receptor/emp1_af/emp1_af.pdb \
  "COS" \
  "1,2" \
  'A:TYR128' \
  --outdir /work/08944/fuzzy/share/covalent_emp1_af \
  --nodes 2 \
  --email fei.yuan@bcm.edu \
  --partition gpu-a100 \
  --project CHE23039
```

## Notes
1. Make sure you activated the virtual environment as shown in the first step. 
2. After successfully run covalent-docking utility with required and/or optional 
    arguments, your covalent docking job should be submitted to the job queue 
    for actual processing. In case you did not see a message indicates your job 
    was successfully submitted, check the error message and re-run the command 
    after you addressed the errors accordingly.
3. For all optional arguments, if you are not sure what value needs to be assigned, 
    just ignore them and let the utility fill the default ones for you.
4. The utility was only tested on lonestar6, it may or may not work on other TACC 
    HPC. In case you encounter any error on other TACC HPC, send the error message 
    to fei.yuan@bcm.edu.
