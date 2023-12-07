#!/usr/bin/env bash

source /work/08944/fuzzy/share/software/covalent-docking/venv/bin/activate

covalent-docking \
  /work/08944/fuzzy/share/chemical_library/covalent_docking/Enamine_Covalent_Compounds_SulfonylFloride_Fluorosulfates_20230811_3d.sdf \
  /work/08944/fuzzy/share/receptor/emp1_af/emp1_af.pdb \
  "COS" \
  "1,2" \
  'A:TYR128' \
  --outdir /work/08944/fuzzy/share/covalent_emp1_af \
  --nodes 4 \
  --email fei.yuan@bcm.edu \
  --partition vs-small \
  --hold