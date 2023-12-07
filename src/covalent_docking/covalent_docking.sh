#!/usr/bin/env bash

# set -e

read -r -d '' usage << EOF
Covalent Docking using AutoDock4

Usage:

  covalent_docking ligand receptor indices residue

    - ligand     Path to ligand in pdbqt format
    - receptor   Path to receptor in pdb format
    - smarts     The SMARTS pattern for the ligand, i.e., C(=O)-O-C
    - indices    The atom indices in the ligand file, i.e., 1,2
    - residue    The residue name and number (Chain:ResNum), i.e., B:SER222
    - outdir     Path to a directory for saving output files
EOF

if [[ $# == 0 ]]
then
  echo "${usage}"
  exit 0
else
  if [[ $# != 6 ]]
  then
    echo "${usage}"
    exit 1
  fi
fi

ligand=$1
receptor=$2
smarts=$3
indices=$4
residue=$5
outdir=$6

cd "${outdir}" || { "Failed to cd into ${outdir}"; exit 1; }
date +"[%D %T] Working and output directory was setting to ${outdir}"

OPENBABEL="${OPENBABEL:=/work/08944/fuzzy/share/software/openbabel/bin}"
export PATH="${OPENBABEL}":$PATH

date +"[%D %T] Preparing inputs"
if [ -f ligand.mol2 ]
then
  date +"[%D %T] Ligand ligand.mol2 already exists, skip re-generating"
else
  obabel "${ligand}" -O ligand.mol2 &> /dev/null
fi

if [ -f receptor.pdb ]
then
  date +"[%D %T] Receptor receptor.pdb already exists, skip re-generating"
else
  obabel "${receptor}" -O receptor.pdb &> /dev/null
fi

MGLTOOLS="${MGLTOOLS:=/work/08944/fuzzy/share/software/mgltools}"
AUTODOCK4="${AUTODOCK4:=/work/08944/fuzzy/share/software/autodock4}"
ADCOVALENT="${ADCOVALENT:=/work/08944/fuzzy/share/software/adcovalent}"

pythonsh="${MGLTOOLS}"/bin/pythonsh
prepare_receptor4="${MGLTOOLS}"/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_receptor4.py
prepare_flexreceptor4="${MGLTOOLS}"/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_flexreceptor4.py
prepare_gpf4="${MGLTOOLS}"/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_gpf4.py
prepare_dpf4="${MGLTOOLS}"/MGLToolsPckgs/AutoDockTools/Utilities24/prepare_dpf4.py

autogrid4="${AUTODOCK4}"/autogrid4
autodock4="${AUTODOCK4}"/autodock4

prepare_covalent="${ADCOVALENT}"/prepareCovalent.py

if [ ! -f ligand_covalent.pdb ]
then
  date +"[%D %T] Preparing ligand"
  date +"[%D %T] cd ${outdir} && ${pythonsh} ${prepare_covalent} --ligand ligand.mol2 --ligindices ${indices} --ligsmart ${smarts}  --receptor receptor.pdb --residue ${residue} --outputfile ligand_covalent.pdb"
  "${pythonsh}" "${prepare_covalent}" \
    --ligand ligand.mol2 \
    --ligindices "${indices}" \
    --ligsmart "${smarts}" \
    --receptor receptor.pdb \
    --residue "${residue}" \
    --outputfile ligand_covalent.pdb &> /dev/null
fi

if [ ! -f ligand_covalent.pdb ]
then
  date +"[%D %T] File ligand_covalent.pdb does not exist, exit"
  exit 1
fi

date +"[%D %T] Preparing receptor"
if [ ! -f receptor.pdbqt ]
then
  "${pythonsh}" "${prepare_receptor4}" -r receptor.pdb -A hydrogens > /dev/null
fi

if [ ! -f ligand_covalent.pdbqt ]
then
  "${pythonsh}" "${prepare_receptor4}" -r ligand_covalent.pdb > /dev/null
fi

if [ ! -f receptor_rigid.pdbqt ]
then
  "${pythonsh}" "${prepare_flexreceptor4}" -r receptor.pdbqt -s receptor:"${residue}" > /dev/null
fi

if [ ! -f ligand_covalent_flex.pdbqt ]
then
  "${pythonsh}" "${prepare_flexreceptor4}" -r ligand_covalent.pdbqt -s ligand_covalent:"${residue}" > /dev/null
fi

if [ ! -f receptor.gpf ]
then
  date +"[%D %T] Preparing gpf file"
  "${pythonsh}" "${prepare_gpf4}" \
    -r receptor_rigid.pdbqt \
    -x ligand_covalent_flex.pdbqt \
    -l ligand_covalent_flex.pdbqt \
    -y -I 20 \
    -o receptor.gpf > /dev/null
fi

if [ ! -f ligand_covalent.dpf ]
then
  date +"[%D %T] Preparing dpf file"
  "${pythonsh}" "${prepare_dpf4}" \
    -r receptor_rigid.pdbqt \
    -x ligand_covalent_flex.pdbqt \
    -l ligand_covalent_flex.pdbqt \
    -p move='empty' \
    -o ligand_covalent.dpf > /dev/null
fi

touch empty
sed -i 's/unbound_model bound/unbound_energy 0.0/' ligand_covalent.dpf
sed -i 's/unbound_model extended/unbound_energy 0.0    /' ligand_covalent.dpf

date +"[%D %T] Docking ..."
if [ ! -f receptor.glg ]
then
  "${autogrid4}" -p receptor.gpf -l receptor.glg &> /dev/null
fi

if [ ! -f ligand_covalent.dlg ]
then
  "${autodock4}" -p ligand_covalent.dpf -l ligand_covalent.dlg &> /dev/null
fi

date +"[%D %T] Docking complete"
