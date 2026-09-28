#!/bin/zsh
# Figures for docs/assembly.md (docs/img/asm) and docs/calibration.md (docs/img/cal).
# Usage: figures.sh [name ...]   (no names: all of them; about 30 minutes on an M-series Mac)
set -e
cd "${0:A:h}/.."
PY="$PWD/.venv/bin/python"
B=/Applications/Blender.app/Contents/MacOS/Blender
R=out/figs_png; mkdir -p $R
( cd cad && $PY figures.py "$@" )
names=("$@"); [[ ${#names} -eq 0 ]] && names=(out/figs/*(/:t))
for n in $names; do
  d=out/figs/$n
  read view dist expo aspect dir <<< $($PY -c "import json;j=json.load(open('$d/points.json'));print(','.join(map(str,j['view'])),j.get('dist',4.3),j.get('expo',-2.4),j.get('aspect',0.75),j['doc'])")
  env SEALGREY=1 LIGHTSCALE=1 FSTOP=90 EXPO=$expo DIST=$dist ASPECT=$aspect PTS=$d/points.json $B -b -P render/white.py -- $d/manifest.json $R/fig_$n.png $view 64 1600 >/dev/null 2>&1
  $PY render/annotate.py docs/img/$dir $R/fig_$n.png
done
