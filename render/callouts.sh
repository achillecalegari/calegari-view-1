#!/bin/zsh
# Lettered part maps for docs/assembly.md (about 10 minutes). Usage: callouts.sh [sheet ...]
set -e
cd "${0:A:h}/.."
PY="$PWD/.venv/bin/python"
B=/Applications/Blender.app/Contents/MacOS/Blender
R=out/callouts; mkdir -p $R
( cd cad && $PY callouts.py "$@" )
sheets=("$@"); [[ ${#sheets} -eq 0 ]] && sheets=(out/mesh_cal_*(:t:s/mesh_cal_//))
for s in $sheets; do
  d=out/mesh_cal_$s
  read view dist expo <<< $($PY -c "import json;j=json.load(open('$d/points.json'));print(','.join(map(str,j['view'])),j.get('dist',4.3),j.get('expo',-2.4))")
  env EXPO=$expo DIST=$dist ASPECT=0.75 PTS=$d/points.json $B -b -P render/white.py -- $d/manifest.json $R/cal_$s.png $view 64 1600 >/dev/null 2>&1
  $PY render/letter.py docs/img/parts $R/cal_$s.png
done
